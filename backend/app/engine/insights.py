"""Turn detector output into ranked, explainable insight cards."""

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from .detect import SavingIncrease, SpendingIncrease, detect_saving_increase, detect_spending_increases
from .texts import SAVING_QUESTION, SPENDING_QUESTION, saving_headline, spending_headline
from .types import Txn

HIDDEN_RESPONSES = frozenset({"one_off", "wrong_category", "dismissed", "goal_created"})
MAX_VISIBLE = 3


@dataclass(frozen=True)
class Insight:
    key: str
    type: Literal["spending", "saving"]
    headline: str
    question: str
    priority: int
    spending: SpendingIncrease | None = None
    saving: SavingIncrease | None = None


def compute_insights(
    txns: Sequence[Txn], savings_ids: frozenset[int], analysis_month: date, first_full: date
) -> list[Insight]:
    found = [
        Insight(s.key, "spending", spending_headline(s), SPENDING_QUESTION, s.priority, spending=s)
        for s in detect_spending_increases(txns, analysis_month, first_full)
    ]
    saving = detect_saving_increase(txns, savings_ids, analysis_month, first_full)
    if saving is not None:
        found.append(Insight(saving.key, "saving", saving_headline(saving), SAVING_QUESTION, saving.priority, saving=saving))
    return sorted(found, key=lambda i: (-i.priority, i.key))


def visible_insights(insights: Sequence[Insight], feedback: dict[str, str]) -> list[Insight]:
    return [i for i in insights if feedback.get(i.key) not in HIDDEN_RESPONSES][:MAX_VISIBLE]
