"""Monthly totals and the customer's personal baseline."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from .money import add_months, median_int, month_of
from .types import Kind, Txn

BASELINE_MAX_MONTHS = 6
BASELINE_MIN_MONTHS = 3


def analysis_month(as_of: date) -> date:
    """The month we analyse: the month of `as_of` if it is complete, otherwise the month before."""
    month = month_of(as_of)
    if add_months(month, 1).toordinal() - 1 == as_of.toordinal():
        return month
    return add_months(month, -1)


def first_full_month(earliest_booked: date) -> date:
    start = month_of(earliest_booked)
    return start if earliest_booked.day == 1 else add_months(start, 1)


def baseline_months(before: date, first_full: date) -> list[date]:
    """Up to 6 months immediately before `before`, oldest first, never earlier than `first_full`."""
    candidates = [add_months(before, -i) for i in range(BASELINE_MAX_MONTHS, 0, -1)]
    return [m for m in candidates if m >= first_full]


def monthly_spend(txns: Iterable[Txn], category: str, include_recurring: bool = True) -> dict[date, int]:
    """Net spending per month for one category, as positive cents. Refunds reduce it; transfers never count."""
    totals: dict[date, int] = defaultdict(int)
    for t in txns:
        if t.category != category or t.kind not in (Kind.EXPENSE, Kind.REFUND):
            continue
        if t.recurring and not include_recurring:
            continue
        totals[month_of(t.booked_on)] -= t.amount_cents
    return dict(totals)


def monthly_income(txns: Iterable[Txn]) -> dict[date, int]:
    totals: dict[date, int] = defaultdict(int)
    for t in txns:
        if t.kind == Kind.INCOME:
            totals[month_of(t.booked_on)] += t.amount_cents
    return dict(totals)


def monthly_net_savings(txns: Iterable[Txn], savings_ids: frozenset[int]) -> dict[date, int]:
    """Money moved into savings accounts minus money moved out, per month."""
    totals: dict[date, int] = defaultdict(int)
    for t in txns:
        if t.kind == Kind.INTERNAL_TRANSFER and t.account_id in savings_ids:
            totals[month_of(t.booked_on)] += t.amount_cents
    return dict(totals)


@dataclass(frozen=True)
class Baseline:
    months: tuple[date, ...]
    low: int
    high: int
    typical: int


def baseline_for(per_month: dict[date, int], months: list[date]) -> Baseline | None:
    if len(months) < BASELINE_MIN_MONTHS:
        return None
    values = [per_month.get(m, 0) for m in months]
    return Baseline(tuple(months), min(values), max(values), median_int(values))
