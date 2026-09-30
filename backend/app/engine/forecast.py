"""Cash-flow scenarios for the current account, 1-3 months ahead.

Transparent by construction: every month's net is the sum of its listed lines.
Scheduled items come from the recurring schedule (confirmed unless their amount varies);
day-to-day spending is estimated from the usual non-recurring spending per category.
"""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from .baseline import baseline_months, monthly_spend
from .money import add_months, median_int
from .types import SPENDING_CATEGORIES, RecurringItem, Txn, category_adjective, category_name

MAX_FORECAST_MONTHS = 3


@dataclass(frozen=True)
class ForecastInputs:
    start_balance: int  # current account
    savings_balance: int
    cash_buffer: int
    schedule: tuple[RecurringItem, ...]
    variable_typical: dict[str, int]  # usual non-recurring spending per category per month (positive)
    variable_months: tuple[date, ...]  # months the estimates are based on


@dataclass(frozen=True)
class ForecastLine:
    label: str
    amount_cents: int  # + money in, - money out
    confirmed: bool


@dataclass(frozen=True)
class MonthProjection:
    month: date
    lines: tuple[ForecastLine, ...]
    start_balance: int
    net: int
    end_balance: int


@dataclass(frozen=True)
class Scenario:
    name: str  # "one_off" | "continues"
    months: tuple[MonthProjection, ...]
    cumulative_net: int
    min_balance: int
    below_buffer: bool
    savings_transfer_may_be_needed: bool


def build_inputs(
    txns: Sequence[Txn],
    schedule: Sequence[RecurringItem],
    *,
    current_balance: int,
    savings_balance: int,
    cash_buffer: int,
    analysis_month: date,
    first_full: date,
) -> ForecastInputs:
    months = baseline_months(analysis_month, first_full)
    variable: dict[str, int] = {}
    for category in sorted(SPENDING_CATEGORIES):
        per_month = monthly_spend(txns, category, include_recurring=False)
        typical = median_int([per_month.get(m, 0) for m in months])
        if typical > 0:
            variable[category] = typical
    return ForecastInputs(
        start_balance=current_balance,
        savings_balance=savings_balance,
        cash_buffer=cash_buffer,
        schedule=tuple(schedule),
        variable_typical=variable,
        variable_months=tuple(months),
    )


def month_lines(inputs: ForecastInputs, month: date, extra: ForecastLine | None = None) -> tuple[ForecastLine, ...]:
    lines = [ForecastLine(i.label, i.amount_cents, i.confirmed) for i in inputs.schedule if i.active_in(month)]
    lines += [ForecastLine(category_name(c), -amount, False) for c, amount in inputs.variable_typical.items()]
    if extra is not None:
        lines.append(extra)
    return tuple(lines)


def project(
    inputs: ForecastInputs, name: str, months: int, start_month: date, extra: ForecastLine | None = None
) -> Scenario:
    if not 1 <= months <= MAX_FORECAST_MONTHS:
        raise ValueError("months must be between 1 and 3")
    balance = inputs.start_balance
    rows: list[MonthProjection] = []
    for i in range(months):
        month = add_months(start_month, i)
        lines = month_lines(inputs, month, extra)
        net = sum(line.amount_cents for line in lines)
        rows.append(MonthProjection(month, lines, balance, net, balance + net))
        balance += net
    min_balance = min(row.end_balance for row in rows)
    below = min_balance < inputs.cash_buffer
    return Scenario(
        name=name,
        months=tuple(rows),
        cumulative_net=sum(row.net for row in rows),
        min_balance=min_balance,
        below_buffer=below,
        savings_transfer_may_be_needed=below and inputs.savings_balance > 0,
    )


def compare(
    inputs: ForecastInputs, category: str, this_month: int, typical: int, months: int, start_month: date
) -> tuple[Scenario, Scenario]:
    """'One-off': spending goes back to usual. 'Continues': this month's level carries on."""
    extra = ForecastLine(f"Extra {category_adjective(category)} spending", -(this_month - typical), False)
    return (
        project(inputs, "one_off", months, start_month),
        project(inputs, "continues", months, start_month, extra),
    )
