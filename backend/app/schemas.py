"""Request and response models. Request bodies reject unknown fields."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .engine.types import SPENDING_CATEGORIES, GoalKind


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


BudgetStatus = Literal["high", "above", "ok"]


class BudgetCategoryOut(BaseModel):
    category: str
    label: str
    amount_cents: int
    typical_cents: int
    usual_low_cents: int
    usual_high_cents: int
    status: BudgetStatus
    note: str
    history: list[MonthAmountOut]
    insight_key: str | None
    noted: bool


class BudgetOut(BaseModel):
    month: str
    total_cents: int
    typical_total_cents: int
    status: BudgetStatus
    note: str
    categories: list[BudgetCategoryOut]
    coverage_note: str


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


MAX_TARGET_CENTS = 1_000_000_000  # €10,000,000
MAX_MONTHLY_CENTS = 10_000_000  # €100,000


class GoalIn(Strict):
    kind: GoalKind
    name: str = Field(min_length=1, max_length=60)
    target_cents: int = Field(gt=0, le=MAX_TARGET_CENTS)
    target_date: date | None = None
    earmarked_cents: int = Field(default=0, ge=0, le=MAX_TARGET_CENTS)
    monthly_contribution_cents: int = Field(default=0, ge=0, le=MAX_MONTHLY_CENTS)
    from_insight: str | None = Field(default=None, max_length=64, pattern=KEY_PATTERN)


class GoalPatch(Strict):
    name: str | None = Field(default=None, min_length=1, max_length=60)
    target_cents: int | None = Field(default=None, gt=0, le=MAX_TARGET_CENTS)
    target_date: date | None = None
    earmarked_cents: int | None = Field(default=None, ge=0, le=MAX_TARGET_CENTS)
    monthly_contribution_cents: int | None = Field(default=None, ge=0, le=MAX_MONTHLY_CENTS)

    @model_validator(mode="after")
    def _no_nulls_except_date(self) -> "GoalPatch":
        for field in self.model_fields_set - {"target_date"}:
            if getattr(self, field) is None:
                raise ValueError(f"{field} can't be empty.")
        return self


class GoalEstimateIn(Strict):
    kind: GoalKind
    target_cents: int = Field(gt=0, le=MAX_TARGET_CENTS)
    target_date: date | None = None
    earmarked_cents: int = Field(default=0, ge=0, le=MAX_TARGET_CENTS)
    monthly_contribution_cents: int = Field(default=0, ge=0, le=MAX_MONTHLY_CENTS)
    name: str | None = Field(default=None, max_length=60)  # ignored; lets the client send the same body
    goal_id: int | None = Field(default=None, gt=0, le=2_147_483_647)


class GoalPlanOut(BaseModel):
    remaining_cents: int
    months_needed: int | None
    estimated_completion: date | None
    required_monthly_cents: int | None
    on_track: bool | None
    progress_pct: int


class NextStepOut(BaseModel):
    title: str
    reason: str


class GoalOut(BaseModel):
    id: int
    kind: GoalKind
    name: str
    target_cents: int
    target_date: date | None
    earmarked_cents: int
    monthly_contribution_cents: int
    plan: GoalPlanOut
    next_steps: list[NextStepOut]


class GoalsOut(BaseModel):
    goals: list[GoalOut]
    available_to_earmark_cents: int
    suggested_monthly_cents: int
    verify_note: str


class GoalEstimateOut(BaseModel):
    plan: GoalPlanOut
    next_steps: list[NextStepOut]
    verify_note: str
