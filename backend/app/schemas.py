"""Request and response models. Request bodies reject unknown fields."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .engine.types import SPENDING_CATEGORIES


class Strict(BaseModel):
    """Base for request bodies: unknown fields are rejected and strings are trimmed."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class LoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")  # passwords are not trimmed
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class MeOut(BaseModel):
    display_name: str


KEY_PATTERN = r"^(spend:[a-z_]{1,40}|saving):\d{4}-\d{2}$"
FeedbackResponse = Literal["one_off", "ongoing", "wrong_category", "dismissed"]


class AccountOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    number: str
    type: str
    balance_cents: int


class InsightCardOut(BaseModel):
    key: str
    type: Literal["spending", "saving"]
    headline: str
    noted: bool


class OverviewOut(BaseModel):
    display_name: str
    as_of: date
    accounts: list[AccountOut]
    insights: list[InsightCardOut]
    coverage_note: str


class MonthAmountOut(BaseModel):
    month: str
    amount_cents: int


class TxnOut(BaseModel):
    id: int
    booked_on: date
    counterparty: str
    amount_cents: int
    category: str


class CategoryOptionOut(BaseModel):
    value: str
    label: str


class InsightDetailOut(BaseModel):
    key: str
    type: Literal["spending", "saving"]
    headline: str
    question: str
    category: str | None
    history: list[MonthAmountOut]
    this_month_cents: int
    typical_cents: int
    usual_low_cents: int | None
    usual_high_cents: int | None
    transactions: list[TxnOut]
    evidence: list[str]
    feedback: str | None
    category_options: list[CategoryOptionOut]
    coverage_note: str


class FeedbackIn(Strict):
    response: FeedbackResponse
    corrected_category: str | None = Field(default=None, max_length=40)

    @model_validator(mode="after")
    def _category_only_with_wrong_category(self) -> "FeedbackIn":
        if self.response == "wrong_category":
            if self.corrected_category not in SPENDING_CATEGORIES:
                raise ValueError("Choose the category these payments belong to.")
        elif self.corrected_category is not None:
            raise ValueError("corrected_category is only allowed with wrong_category.")
        return self


class FeedbackOut(BaseModel):
    key: str
    response: str


class LineOut(BaseModel):
    label: str
    amount_cents: int
    confirmed: bool


class MonthOut(BaseModel):
    month: str
    start_balance_cents: int
    net_cents: int
    end_balance_cents: int
    lines: list[LineOut]


class ScenarioOut(BaseModel):
    name: str
    months: list[MonthOut]
    cumulative_net_cents: int
    min_balance_cents: int
    below_buffer: bool
    savings_transfer_may_be_needed: bool


class ScenarioResponseOut(BaseModel):
    key: str
    months: int
    cash_buffer_cents: int
    one_off: ScenarioOut
    continues: ScenarioOut
    assumptions: list[str]
    coverage_note: str
