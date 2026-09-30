"""Next steps per confirmed goal. Planning help only: nothing here applies for or executes a product."""

from dataclasses import dataclass

from .money import fmt_eur
from .types import GoalKind

VERIFY_NOTE = "Terms, eligibility and availability to be verified."


@dataclass(frozen=True)
class NextStep:
    title: str
    reason: str


_SAVINGS_PLAN = NextStep(
    "Set up a monthly savings plan",
    "Saving the same amount every month keeps you on the timeline shown above.",
)


def next_steps(kind: GoalKind, typical_monthly_spending_cents: int) -> tuple[NextStep, ...]:
    if kind is GoalKind.CAR:
        return (
            _SAVINGS_PLAN,
            NextStep(
                "Compare car financing (illustrative)",
                "Useful if you want to see how financing part of the car compares with saving the full amount. Nothing is applied for.",
            ),
        )
    if kind is GoalKind.HOME:
        return (
            NextStep("Plan your upfront costs", "A home purchase usually needs savings for the deposit, registration tax and notary fees."),
            NextStep(
                "Housing affordability tool",
                "Shows what you might be able to borrow. Goal progress alone doesn't establish mortgage affordability.",
            ),
        )
    if kind is GoalKind.EMERGENCY:
        if typical_monthly_spending_cents > 0:
            target_reason = f"A common rule of thumb is three months of spending: about {fmt_eur(3 * typical_monthly_spending_cents)} for you."
        else:
            target_reason = "A common rule of thumb is three months of your usual spending."
        return (
            NextStep("Automate a monthly transfer", "An automatic transfer builds the fund without you having to remember it."),
            NextStep("Suggested target: 3 × monthly spending", target_reason),
        )
    return (_SAVINGS_PLAN,)
