"""Glue between customer data and the engine. No HTTP here."""

from .engine.baseline import baseline_months, monthly_net_savings, monthly_spend
from .engine.detect import RECENT_MONTHS, SavingIncrease, SpendingIncrease
from .engine.forecast import ForecastInputs, build_inputs
from .engine.insights import Insight, compute_insights
from .engine.money import add_months, median_int, month_of
from .engine.types import SPENDING_CATEGORIES, Kind, Txn
from .repo import CustomerData


def all_insights(data: CustomerData | None) -> list[Insight]:
    if data is None:
        return []
    return compute_insights(data.txns, data.savings_ids, data.analysis_month, data.first_full_month)


def find_insight(data: CustomerData | None, key: str) -> Insight | None:
    return next((i for i in all_insights(data) if i.key == key), None)


def forecast_inputs(data: CustomerData) -> ForecastInputs:
    return build_inputs(
        data.txns,
        data.schedule,
        current_balance=data.current_balance,
        savings_balance=data.savings_balance,
        cash_buffer=data.cash_buffer,
        analysis_month=data.analysis_month,
        first_full=data.first_full_month,
    )


def spending_transactions(data: CustomerData, s: SpendingIncrease) -> list[Txn]:
    """The transactions behind a spending insight: that category in that month, refunds included."""
    return [
        t
        for t in data.txns
        if t.category == s.category and t.kind in (Kind.EXPENSE, Kind.REFUND) and month_of(t.booked_on) == s.month
    ]


def saving_transactions(data: CustomerData, s: SavingIncrease) -> list[Txn]:
    recent = set(s.recent_months)
    return [
        t
        for t in data.txns
        if t.kind == Kind.INTERNAL_TRANSFER and t.account_id in data.savings_ids and month_of(t.booked_on) in recent
    ]


def typical_monthly_spending(data: CustomerData | None) -> int:
    if data is None:
        return 0
    months = baseline_months(data.analysis_month, data.first_full_month)
    total = 0
    for category in SPENDING_CATEGORIES:
        per_month = monthly_spend(data.txns, category)
        total += median_int([per_month.get(m, 0) for m in months])
    return total


def suggested_monthly_saving(data: CustomerData | None) -> int:
    if data is None:
        return 0
    per_month = monthly_net_savings(data.txns, data.savings_ids)
    recent = [add_months(data.analysis_month, -i) for i in range(RECENT_MONTHS)]
    return max(0, median_int([per_month.get(m, 0) for m in recent]))
