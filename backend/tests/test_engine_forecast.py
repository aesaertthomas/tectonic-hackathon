from datetime import date

import pytest

from app.engine.forecast import ForecastInputs, ForecastLine, build_inputs, compare, project
from tests.factories import MAR, OCT, SEP, item, monthly

NOV = date(2026, 11, 1)
DEC = date(2026, 12, 1)


def brief_inputs(savings_balance: int = 300_000) -> ForecastInputs:
    """The brief's example: usual surplus €150, groceries usually €350."""
    return ForecastInputs(
        start_balance=65_000,
        savings_balance=savings_balance,
        cash_buffer=50_000,
        schedule=(item("Salary", 2500, confirmed=False), item("Rent and bills", -1400)),
        variable_typical={"food": 35_000, "other": 60_000},
        variable_months=(),
    )


def test_brief_example_one_off_versus_continues():
    one_off, continues = compare(brief_inputs(), "food", this_month=60_000, typical=35_000, months=3, start_month=OCT)

    assert [m.net for m in one_off.months] == [15_000, 15_000, 15_000]
    assert [m.end_balance for m in one_off.months] == [80_000, 95_000, 110_000]
    assert one_off.cumulative_net == 45_000
    assert not one_off.below_buffer and not one_off.savings_transfer_may_be_needed

    assert [m.net for m in continues.months] == [-10_000, -10_000, -10_000]
    assert [m.end_balance for m in continues.months] == [55_000, 45_000, 35_000]
    assert continues.cumulative_net == -30_000
    assert continues.min_balance == 35_000
    assert continues.below_buffer and continues.savings_transfer_may_be_needed


def test_continues_adds_one_estimated_extra_line():
    _, continues = compare(brief_inputs(), "food", 60_000, 35_000, 1, OCT)
    assert continues.months[0].lines[-1] == ForecastLine("Extra grocery spending", -25_000, False)


def test_confirmed_and_estimated_lines_are_distinguished():
    one_off, _ = compare(brief_inputs(), "food", 60_000, 35_000, 1, OCT)
    by_label = {line.label: line for line in one_off.months[0].lines}
    assert by_label["Rent and bills"].confirmed is True
    assert by_label["Salary"].confirmed is False
    assert by_label["Groceries"].confirmed is False


def test_no_transfer_warning_without_savings():
    _, continues = compare(brief_inputs(savings_balance=0), "food", 60_000, 35_000, 3, OCT)
    assert continues.below_buffer is True
    assert continues.savings_transfer_may_be_needed is False


def test_yearly_items_only_count_in_their_month():
    inputs = ForecastInputs(
        start_balance=0,
        savings_balance=0,
        cash_buffer=0,
        schedule=(item("Year-end bonus", 4000, "yearly", (12,)), item("After-school care", -175, "monthly_except", (1, 2, 3, 4, 5, 6, 9, 10, 11, 12))),
        variable_typical={},
        variable_months=(),
    )
    scenario = project(inputs, "one_off", 3, OCT)
    assert [m.month for m in scenario.months] == [OCT, NOV, DEC]
    assert [m.net for m in scenario.months] == [-17_500, -17_500, 382_500]
    assert not item("After-school care", -175, "monthly_except", (9, 10)).active_in(date(2026, 7, 1))


@pytest.mark.parametrize("months", [0, 4])
def test_months_must_be_one_to_three(months):
    with pytest.raises(ValueError):
        compare(brief_inputs(), "food", 60_000, 35_000, months, OCT)


def test_build_inputs_uses_non_recurring_spending_only():
    txns = (
        monthly(MAR, [340, 380, 300, 400, 350, 350, 600], "food")
        + monthly(MAR, [112] * 7, "transport", recurring=True)  # the train pass is in the schedule instead
        + monthly(MAR, [300, 290, 310, 300, 305, 295, 300], "transport", day=15)
        + monthly(MAR, [0] * 7, "clothing")
    )
    schedule = (item("NMBS pass", -112, category="transport"),)
    inputs = build_inputs(
        txns, schedule, current_balance=93_539, savings_balance=1, cash_buffer=100_000, analysis_month=SEP, first_full=MAR
    )
    assert inputs.variable_typical == {"food": 35_000, "transport": 30_000}
    assert inputs.schedule == schedule
    assert inputs.variable_months[0] == MAR and len(inputs.variable_months) == 6
