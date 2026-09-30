"""Goal timelines. Estimates only: they assume the monthly contribution is kept up."""

from dataclasses import dataclass
from datetime import date

from .money import add_months, ceil_div, month_of, months_between


@dataclass(frozen=True)
class GoalPlan:
    remaining_cents: int
    months_needed: int | None
    estimated_completion: date | None  # first day of the month
    required_monthly_cents: int | None
    on_track: bool | None
    progress_pct: int


def plan_goal(
    *,
    target_cents: int,
    earmarked_cents: int,
    monthly_contribution_cents: int,
    target_date: date | None,
    as_of: date,
) -> GoalPlan:
    remaining = max(0, target_cents - earmarked_cents)
    progress = min(100, earmarked_cents * 100 // target_cents) if target_cents > 0 else 0
    start = month_of(as_of)
    months_needed: int | None
    completion: date | None
    if remaining == 0:
        months_needed, completion = 0, start
    elif monthly_contribution_cents > 0:
        months_needed = ceil_div(remaining, monthly_contribution_cents)
        completion = add_months(start, months_needed)
    else:
        months_needed, completion = None, None
    required: int | None = None
    on_track: bool | None = None
    if target_date is not None:
        months_left = max(1, months_between(start, month_of(target_date)))
        required = ceil_div(remaining, months_left)
        on_track = monthly_contribution_cents >= required
    return GoalPlan(remaining, months_needed, completion, required, on_track, progress)
