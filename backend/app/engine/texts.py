"""Customer-facing copy. Calm, specific, free of judgment. Amounts always come from the engine."""

from .budget import ABOVE_USUAL_PERCENT, CategoryBudget
from .detect import SavingIncrease, SpendingIncrease
from .forecast import ForecastInputs
from .money import fmt_eur
from .types import category_adjective

COVERAGE_NOTE = "Based on your KBC accounts only. Cash spending and other banks are not included."
SPENDING_QUESTION = "Was this a one-off, or do you expect it to continue?"
SAVING_QUESTION = "Would you like to connect this to a goal?"


def spending_headline(s: SpendingIncrease) -> str:
    return (
        f"Your {category_adjective(s.category)} spending was {fmt_eur(s.amount)} in {s.month:%B}. "
        f"Your usual range is {fmt_eur(s.baseline.low)}–{fmt_eur(s.baseline.high)}."
    )


def spending_evidence(s: SpendingIncrease) -> list[str]:
    first, last = s.baseline.months[0], s.baseline.months[-1]
    lines = [
        f"We compared {s.month:%B} with your previous {len(s.baseline.months)} months ({first:%B}–{last:%B %Y}).",
        f"In those months you spent between {fmt_eur(s.baseline.low)} and {fmt_eur(s.baseline.high)}, typically {fmt_eur(s.baseline.typical)}.",
    ]
    if s.last_year is not None:
        lines.append(f"Last {s.month:%B} you spent {fmt_eur(s.last_year)}, so this isn't a usual seasonal rise.")
    lines += [
        "We only mention a change when a month is more than 20% above your usual high and at least €50 above your typical month.",
        "Transfers between your own accounts and credit-card repayments are left out, and refunds are deducted, so nothing is counted twice.",
    ]
    return lines


def saving_headline(s: SavingIncrease) -> str:
    return (
        "You've increased your monthly saving contributions from around "
        f"{fmt_eur(s.reference_typical)} to {fmt_eur(s.recent_typical)}."
    )


def saving_evidence(s: SavingIncrease) -> list[str]:
    first, last = s.recent_months[0], s.recent_months[-1]
    if s.basis == "year_ago":
        compared = f"the same months last year ({s.reference_months[0]:%B}–{s.reference_months[-1]:%B %Y})"
    else:
        compared = f"the months before ({s.reference_months[0]:%B}–{s.reference_months[-1]:%B %Y})"
    return [
        f"From {first:%B} to {last:%B %Y} you moved at least 50% more into savings each month than in {compared}.",
        "We count money moved into your savings accounts minus money taken out.",
        "Moving money into savings isn't the same as your wealth growing: it's money you set aside.",
        "We don't assume what you're saving for. You choose.",
    ]


def forecast_assumptions(inputs: ForecastInputs, s: SpendingIncrease) -> list[str]:
    adjective = category_adjective(s.category)
    variable_total = sum(inputs.variable_typical.values())
    items = [
        "Regular income and payments come from your scheduled items. Amounts that vary, like salary, are estimates.",
        "Yearly items, such as a year-end bonus or property tax, are only included in the month they're due.",
    ]
    if inputs.variable_months:
        items.append(
            f"Day-to-day spending of about {fmt_eur(variable_total)} a month is estimated from your usual months "
            f"({inputs.variable_months[0]:%B}–{inputs.variable_months[-1]:%B %Y})."
        )
    items += [
        f"If it's a one-off, {adjective} spending goes back to about {fmt_eur(s.baseline.typical)}. "
        f"If it continues, it stays at {fmt_eur(s.amount)} a month.",
        "Credit-card purchases are counted in the month you make them.",
        "Occasional income, such as interest or refunds, isn't included.",
        "Everything else stays the same.",
        f"You want to keep at least {fmt_eur(inputs.cash_buffer)} in your current account.",
        COVERAGE_NOTE,
    ]
    return items


NO_HISTORY_NOTE = "We need at least three full months of history before we can compare with your usual month."


def _clearly_below(amount: int, typical: int) -> bool:
    return amount * 100 < typical * (100 - ABOVE_USUAL_PERCENT)


def budget_note(b: CategoryBudget) -> str:
    if b.status == "high":
        return f"{fmt_eur(b.amount)} this month, above your usual range of {fmt_eur(b.low)}–{fmt_eur(b.high)}."
    if b.status == "above":
        return f"{fmt_eur(b.amount - b.typical)} more than your usual month."
    if _clearly_below(b.amount, b.typical):
        return f"{fmt_eur(b.typical - b.amount)} less than your usual month."
    return "In line with your usual month."


def month_note(total: int, typical: int) -> str:
    if total * 100 > typical * (100 + ABOVE_USUAL_PERCENT):
        return f"You spent {fmt_eur(total - typical)} more than in a usual month."
    if _clearly_below(total, typical):
        return f"You spent {fmt_eur(typical - total)} less than in a usual month."
    return "In line with your usual month."
