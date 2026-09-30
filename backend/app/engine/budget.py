"""Each spending category's analysis-month total next to the customer's usual month."""

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from .baseline import BASELINE_MIN_MONTHS, baseline_for, baseline_months, monthly_spend
from .money import add_months
from .types import SPENDING_CATEGORIES, Txn

Status = Literal["high", "above", "ok"]

ABOVE_USUAL_PERCENT = 10  # orange once a month is more than 10% above the usual month
HISTORY_MONTHS = 6
_ORDER: dict[Status, int] = {"high": 0, "above": 1, "ok": 2}


def spend_status(amount: int, typical: int, flagged: bool = False) -> Status:
    """Red only for detector-flagged categories; orange for a clear rise that isn't an insight."""
    if flagged:
        return "high"
    if amount * 100 > typical * (100 + ABOVE_USUAL_PERCENT):
        return "above"
    return "ok"


@dataclass(frozen=True)
class CategoryBudget:
    category: str
    amount: int
    typical: int
    low: int
    high: int
    history: tuple[tuple[date, int], ...]
    status: Status


def category_budgets(
    txns: Sequence[Txn], analysis_month: date, first_full: date, flagged: Collection[str]
) -> list[CategoryBudget]:
    months = baseline_months(analysis_month, first_full)
    if len(months) < BASELINE_MIN_MONTHS:
        return []
    chart = [add_months(analysis_month, -i) for i in range(HISTORY_MONTHS - 1, -1, -1)]
    found: list[CategoryBudget] = []
    for category in sorted(SPENDING_CATEGORIES):
        per_month = monthly_spend(txns, category)
        base = baseline_for(per_month, months)
        amount = per_month.get(analysis_month, 0)
        if base is None or (base.typical <= 0 and amount <= 0):
            continue
        found.append(
            CategoryBudget(
                category=category,
                amount=amount,
                typical=base.typical,
                low=base.low,
                high=base.high,
                history=tuple((m, per_month.get(m, 0)) for m in chart if m >= first_full),
                status=spend_status(amount, base.typical, category in flagged),
            )
        )
    return sorted(found, key=lambda b: (_ORDER[b.status], -b.amount, b.category))
