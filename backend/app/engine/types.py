"""Plain value types shared by the calculation engine. No web or database imports."""

from dataclasses import dataclass
from datetime import date
from enum import StrEnum


class Kind(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"
    REFUND = "refund"
    INTERNAL_TRANSFER = "internal_transfer"


# Spending categories used by the dataset: category -> (display name, adjective for sentences).
SPENDING_LABELS: dict[str, tuple[str, str]] = {
    "food": ("Groceries", "grocery"),
    "housing_energy": ("Housing & energy", "housing"),
    "transport": ("Transport", "transport"),
    "healthcare": ("Healthcare", "healthcare"),
    "insurance_financial_services": ("Insurance & bank fees", "insurance"),
    "leisure_culture": ("Leisure & culture", "leisure"),
    "restaurants": ("Eating out", "eating-out"),
    "household_maintenance": ("Household", "household"),
    "clothing": ("Clothing", "clothing"),
    "communication": ("Phone & internet", "phone and internet"),
    "children_education": ("Children & school", "school"),
    "education": ("Education", "education"),
    "subscriptions": ("Subscriptions", "subscription"),
    "debt_repayment": ("Loan repayments", "loan"),
    "other": ("Other", "other"),
}
SPENDING_CATEGORIES: frozenset[str] = frozenset(SPENDING_LABELS)


def category_name(category: str) -> str:
    return SPENDING_LABELS.get(category, (category.replace("_", " ").capitalize(), ""))[0]


def category_adjective(category: str) -> str:
    return SPENDING_LABELS.get(category, ("", category.replace("_", " ")))[1]


class GoalKind(StrEnum):
    CAR = "car"
    HOME = "home"
    EMERGENCY = "emergency"
    OTHER = "other"


@dataclass(frozen=True)
class Txn:
    id: int
    account_id: int
    booked_on: date
    amount_cents: int  # negative = money leaves the account
    counterparty: str
    category: str
    kind: Kind
    recurring: bool


@dataclass(frozen=True)
class RecurringItem:
    """A scheduled item seen from the current account: + money in, - money out."""

    label: str
    category: str
    amount_cents: int
    frequency: str  # monthly | monthly_except | yearly
    months: tuple[int, ...]  # active months for monthly_except / yearly; empty for monthly
    confirmed: bool  # False when the amount varies from month to month (e.g. salary)

    def active_in(self, month: date) -> bool:
        return self.frequency == "monthly" or month.month in self.months
