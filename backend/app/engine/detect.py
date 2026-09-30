"""Detect meaningful changes. Thresholds are deliberately simple so every insight can be explained."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from .baseline import BASELINE_MIN_MONTHS, Baseline, baseline_for, baseline_months, monthly_net_savings, monthly_spend
from .money import add_months, median_int, month_key
from .types import SPENDING_CATEGORIES, Txn

MIN_SPIKE_CENTS = 5_000  # at least €50 above the typical month
MIN_SAVING_INCREASE_CENTS = 10_000  # at least €100 more per month
RECENT_MONTHS = 3
HISTORY_CHART_MONTHS = 12


def more_than_20_percent_above(amount: int, reference: int) -> bool:
    return amount * 5 > reference * 6


@dataclass(frozen=True)
class SpendingIncrease:
    key: str
    category: str
    month: date
    amount: int
    baseline: Baseline
    last_year: int | None  # same month a year earlier, when the history covers it
    priority: int


@dataclass(frozen=True)
class SavingIncrease:
    key: str
    month: date
    basis: str  # "year_ago" | "before"
    recent_months: tuple[date, ...]
    reference_months: tuple[date, ...]
    recent_typical: int
    reference_typical: int
    history: tuple[tuple[date, int], ...]
    priority: int


def detect_spending_increases(txns: Sequence[Txn], analysis_month: date, first_full: date) -> list[SpendingIncrease]:
    months = baseline_months(analysis_month, first_full)
    if len(months) < BASELINE_MIN_MONTHS:
        return []
    year_ago = add_months(analysis_month, -12)
    found: list[SpendingIncrease] = []
    for category in sorted(SPENDING_CATEGORIES):
        per_month = monthly_spend(txns, category)
        base = baseline_for(per_month, months)
        if base is None or base.typical <= 0:
            continue
        amount = per_month.get(analysis_month, 0)
        if not more_than_20_percent_above(amount, base.high) or amount - base.typical < MIN_SPIKE_CENTS:
            continue
        last_year = per_month.get(year_ago, 0) if year_ago >= first_full else None
        if last_year is not None and not more_than_20_percent_above(amount, last_year):
            continue  # seasonal: a similar rise happened in the same month last year
        found.append(
            SpendingIncrease(
                key=f"spend:{category}:{month_key(analysis_month)}",
                category=category,
                month=analysis_month,
                amount=amount,
                baseline=base,
                last_year=last_year,
                priority=amount - base.typical,
            )
        )
    return found


def detect_saving_increase(
    txns: Sequence[Txn], savings_ids: frozenset[int], analysis_month: date, first_full: date
) -> SavingIncrease | None:
    per_month = monthly_net_savings(txns, savings_ids)
    recent = [add_months(analysis_month, -i) for i in range(RECENT_MONTHS - 1, -1, -1)]
    if recent[0] < first_full:
        return None
    year_ago = [add_months(m, -12) for m in recent]
    if year_ago[0] >= first_full:
        reference, basis = year_ago, "year_ago"
    else:
        reference, basis = baseline_months(recent[0], first_full), "before"
        if len(reference) < 2:
            return None
    reference_typical = median_int([per_month.get(m, 0) for m in reference])
    recent_values = [per_month.get(m, 0) for m in recent]
    recent_typical = median_int(recent_values)
    if recent_typical <= 0 or recent_typical - reference_typical < MIN_SAVING_INCREASE_CENTS:
        return None
    if not all(value * 2 >= reference_typical * 3 for value in recent_values):
        return None
    chart_months = [add_months(analysis_month, -i) for i in range(HISTORY_CHART_MONTHS - 1, -1, -1)]
    return SavingIncrease(
        key=f"saving:{month_key(analysis_month)}",
        month=analysis_month,
        basis=basis,
        recent_months=tuple(recent),
        reference_months=tuple(reference),
        recent_typical=recent_typical,
        reference_typical=reference_typical,
        history=tuple((m, per_month.get(m, 0)) for m in chart_months if m >= first_full),
        priority=(recent_typical - reference_typical) * 3,
    )
