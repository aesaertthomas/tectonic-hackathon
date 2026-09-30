from datetime import date

from app.engine.baseline import (
    Baseline,
    analysis_month,
    baseline_for,
    baseline_months,
    first_full_month,
    monthly_income,
    monthly_net_savings,
    monthly_spend,
)
from app.engine.types import Kind
from tests.factories import AUG, FEB, MAR, SEP, monthly, txn


def test_analysis_month_uses_complete_month_only():
    assert analysis_month(date(2026, 9, 30)) == SEP
    assert analysis_month(date(2026, 9, 29)) == AUG  # September is not complete yet
    assert analysis_month(date(2026, 2, 28)) == FEB


def test_first_full_month():
    assert first_full_month(date(2026, 2, 1)) == FEB
    assert first_full_month(date(2026, 2, 14)) == MAR


def test_baseline_months_are_six_before_and_respect_history_start():
    assert baseline_months(SEP, FEB) == [MAR, date(2026, 4, 1), date(2026, 5, 1), date(2026, 6, 1), date(2026, 7, 1), AUG]
    assert baseline_months(SEP, date(2026, 6, 1)) == [date(2026, 6, 1), date(2026, 7, 1), AUG]


def test_monthly_spend_nets_refunds_and_ignores_transfers():
    txns = [
        txn(date(2026, 9, 3), -60_000, "food"),
        txn(date(2026, 9, 9), 5_000, "food", Kind.REFUND),
        txn(date(2026, 9, 5), -90_000, "food", Kind.INTERNAL_TRANSFER),  # never spending
        txn(date(2026, 9, 6), -1_000, "transport"),
    ]
    assert monthly_spend(txns, "food") == {SEP: 55_000}


def test_monthly_spend_can_exclude_recurring():
    txns = [txn(date(2026, 9, 1), -11_200, "transport", recurring=True), txn(date(2026, 9, 8), -3_000, "transport")]
    assert monthly_spend(txns, "transport") == {SEP: 14_200}
    assert monthly_spend(txns, "transport", include_recurring=False) == {SEP: 3_000}


def test_monthly_income_ignores_internal_transfers():
    txns = [
        txn(date(2026, 9, 1), 230_000, "pension", Kind.INCOME),
        txn(date(2026, 9, 2), 45_000, "transfer_to_savings", Kind.INTERNAL_TRANSFER, account_id=2),
    ]
    assert monthly_income(txns) == {SEP: 230_000}


def test_monthly_net_savings_counts_both_directions_on_savings_accounts_only():
    txns = [
        txn(date(2026, 7, 2), 30_000, "transfer_to_savings", Kind.INTERNAL_TRANSFER, account_id=2),
        txn(date(2026, 7, 2), -30_000, "transfer_to_savings", Kind.INTERNAL_TRANSFER, account_id=1),
        txn(date(2026, 7, 3), -150_000, "transfer_from_savings", Kind.INTERNAL_TRANSFER, account_id=2),
        txn(date(2026, 7, 31), 500, "interest", Kind.INCOME, account_id=2),  # interest is income, not a contribution
    ]
    assert monthly_net_savings(txns, frozenset({2})) == {date(2026, 7, 1): -120_000}


def test_baseline_for_brief_example():
    per_month = {m.replace(day=1): v for m, v in zip(baseline_months(SEP, FEB), [34_000, 38_000, 30_000, 40_000, 35_000, 35_000])}
    base = baseline_for(per_month, baseline_months(SEP, FEB))
    assert base == Baseline(months=tuple(baseline_months(SEP, FEB)), low=30_000, high=40_000, typical=35_000)


def test_baseline_needs_three_months():
    assert baseline_for({}, [date(2026, 7, 1), AUG]) is None


def test_missing_months_count_as_zero():
    txns = monthly(MAR, [100, 100, 100], "clothing")  # Mar-May only
    base = baseline_for(monthly_spend(txns, "clothing"), baseline_months(SEP, FEB))
    assert base is not None and base.low == 0 and base.high == 10_000
