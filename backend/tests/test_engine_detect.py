from datetime import date

from app.engine.detect import detect_saving_increase, detect_spending_increases
from app.engine.types import Kind
from tests.factories import MAR, SEP, monthly

SEP_2025 = date(2025, 9, 1)
JUL_2025 = date(2025, 7, 1)
JAN = date(2026, 1, 1)
JUL = date(2026, 7, 1)


# --- spending ---------------------------------------------------------------------------------

def test_brief_grocery_example_fires():
    txns = monthly(MAR, [340, 380, 300, 400, 350, 350, 600], "food")
    [found] = detect_spending_increases(txns, SEP, MAR)
    assert found.key == "spend:food:2026-09"
    assert found.category == "food"
    assert (found.amount, found.baseline.low, found.baseline.high, found.baseline.typical) == (60_000, 30_000, 40_000, 35_000)
    assert found.last_year is None
    assert found.priority == 25_000


def test_within_twenty_percent_of_usual_high_does_not_fire():
    txns = monthly(MAR, [340, 380, 300, 400, 350, 350, 450], "food")
    assert detect_spending_increases(txns, SEP, MAR) == []


def test_small_absolute_change_does_not_fire():
    txns = monthly(MAR, [10, 10, 10, 10, 10, 10, 40], "clothing")
    assert detect_spending_increases(txns, SEP, MAR) == []


def test_zero_typical_category_never_fires():
    txns = monthly(MAR, [0, 0, 0, 0, 0, 0, 200], "healthcare")
    assert detect_spending_increases(txns, SEP, MAR) == []


def test_needs_three_baseline_months():
    txns = monthly(JUL, [350, 350, 600], "food")
    assert detect_spending_increases(txns, SEP, JUL) == []


def test_seasonal_rise_is_not_flagged():
    # Sep 2025 .. Sep 2026: back-to-school costs every September.
    amounts = [820] + [400] * 10 + [100] + [830]
    txns = monthly(SEP_2025, amounts, "children_education")
    assert detect_spending_increases(txns, SEP, SEP_2025) == []


def test_real_spike_still_fires_when_last_year_was_normal():
    amounts = [920] + [900] * 11 + [1420]
    txns = monthly(SEP_2025, amounts, "food")
    [found] = detect_spending_increases(txns, SEP, SEP_2025)
    assert found.last_year == 92_000


def test_refund_can_cancel_a_spike():
    txns = monthly(MAR, [340, 380, 300, 400, 350, 350, 600], "food") + monthly(SEP, [250], "food", kind=Kind.REFUND)
    assert detect_spending_increases(txns, SEP, MAR) == []


# --- saving -----------------------------------------------------------------------------------

def _savings(first: date, amounts: list[int]):
    return monthly(first, amounts, "transfer_to_savings", kind=Kind.INTERNAL_TRANSFER, account_id=2)


def test_saving_increase_compared_with_same_months_last_year():
    # Jul 2025 .. Sep 2026: 200 until Feb, 300 in Mar-Apr, 450 from May.
    txns = _savings(JUL_2025, [200] * 8 + [300, 300] + [450] * 5)
    found = detect_saving_increase(txns, frozenset({2}), SEP, JUL_2025)
    assert found is not None
    assert found.key == "saving:2026-09"
    assert found.basis == "year_ago"
    assert (found.reference_typical, found.recent_typical) == (20_000, 45_000)
    assert found.recent_months == (JUL, date(2026, 8, 1), SEP)
    assert found.priority == 75_000
    assert len(found.history) == 12 and found.history[-1] == (SEP, 45_000)


def test_saving_increase_falls_back_to_months_before_when_history_is_short():
    txns = _savings(JAN, [200, 200, 300, 300, 450, 450, 450, 450, 450])
    found = detect_saving_increase(txns, frozenset({2}), SEP, JAN)
    assert found is not None
    assert found.basis == "before"
    assert found.reference_typical == 30_000


def test_one_low_recent_month_means_not_sustained():
    txns = _savings(JUL_2025, [200] * 8 + [300, 300] + [450] * 4 + [0])
    assert detect_saving_increase(txns, frozenset({2}), SEP, JUL_2025) is None


def test_increase_below_100_euro_is_ignored():
    txns = _savings(JUL_2025, [200] * 12 + [280] * 3)
    assert detect_saving_increase(txns, frozenset({2}), SEP, JUL_2025) is None


def test_drawing_down_savings_is_not_an_increase():
    txns = _savings(JUL_2025, [300] * 12 + [-1200, 300, 300])
    assert detect_saving_increase(txns, frozenset({2}), SEP, JUL_2025) is None


def test_saving_needs_enough_history():
    txns = _savings(JUL, [450, 450, 450])
    assert detect_saving_increase(txns, frozenset({2}), SEP, JUL) is None


def test_only_savings_accounts_count():
    txns = _savings(JUL_2025, [200] * 8 + [300, 300] + [450] * 5)
    assert detect_saving_increase(txns, frozenset({99}), SEP, JUL_2025) is None
