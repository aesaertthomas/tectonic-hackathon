from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query

from .. import repo, services
from ..deps import CurrentCustomer, DbSession
from ..engine.baseline import monthly_spend
from ..engine.forecast import MAX_FORECAST_MONTHS, Scenario, compare
from ..engine.money import add_months, month_key
from ..engine.texts import COVERAGE_NOTE, forecast_assumptions, saving_evidence, spending_evidence
from ..engine.types import SPENDING_CATEGORIES, Txn, category_name
from ..schemas import (
    KEY_PATTERN,
    CategoryOptionOut,
    FeedbackIn,
    FeedbackOut,
    InsightDetailOut,
    LineOut,
    MonthAmountOut,
    MonthOut,
    ScenarioOut,
    ScenarioResponseOut,
    TxnOut,
)
from .common import load_insight

router = APIRouter(prefix="/api", tags=["insights"])

InsightKey = Annotated[str, Path(max_length=64, pattern=KEY_PATTERN)]


def _txn_out(t: Txn) -> TxnOut:
    return TxnOut(id=t.id, booked_on=t.booked_on, counterparty=t.counterparty, amount_cents=t.amount_cents, category=t.category)


def _scenario_out(s: Scenario) -> ScenarioOut:
    return ScenarioOut(
        name=s.name,
        months=[
            MonthOut(
                month=month_key(m.month),
                start_balance_cents=m.start_balance,
                net_cents=m.net,
                end_balance_cents=m.end_balance,
                lines=[LineOut(label=l.label, amount_cents=l.amount_cents, confirmed=l.confirmed) for l in m.lines],
            )
            for m in s.months
        ],
        cumulative_net_cents=s.cumulative_net,
        min_balance_cents=s.min_balance,
        below_buffer=s.below_buffer,
        savings_transfer_may_be_needed=s.savings_transfer_may_be_needed,
    )


@router.get("/insights/{key}", response_model=InsightDetailOut)
def insight_detail(key: InsightKey, customer: CurrentCustomer, db: DbSession) -> InsightDetailOut:
    data, insight = load_insight(db, customer, key)
    feedback = repo.feedback_map(db, customer.id).get(key)
    if insight.spending is not None:
        s = insight.spending
        per_month = monthly_spend(data.txns, s.category)
        return InsightDetailOut(
            key=key,
            type="spending",
            headline=insight.headline,
            question=insight.question,
            category=s.category,
            history=[MonthAmountOut(month=month_key(m), amount_cents=per_month.get(m, 0)) for m in (*s.baseline.months, s.month)],
            this_month_cents=s.amount,
            typical_cents=s.baseline.typical,
            usual_low_cents=s.baseline.low,
            usual_high_cents=s.baseline.high,
            transactions=[_txn_out(t) for t in services.spending_transactions(data, s)],
            evidence=spending_evidence(s),
            feedback=feedback,
            category_options=[
                CategoryOptionOut(value=c, label=category_name(c))
                for c in sorted(SPENDING_CATEGORIES, key=category_name)
                if c != s.category
            ],
            coverage_note=COVERAGE_NOTE,
        )
    saving = insight.saving
    if saving is None:
        raise HTTPException(status_code=404, detail="Insight not found.")
    return InsightDetailOut(
        key=key,
        type="saving",
        headline=insight.headline,
        question=insight.question,
        category=None,
        history=[MonthAmountOut(month=month_key(m), amount_cents=a) for m, a in saving.history],
        this_month_cents=saving.recent_typical,
        typical_cents=saving.reference_typical,
        usual_low_cents=None,
        usual_high_cents=None,
        transactions=[_txn_out(t) for t in services.saving_transactions(data, saving)],
        evidence=saving_evidence(saving),
        feedback=feedback,
        category_options=[],
        coverage_note=COVERAGE_NOTE,
    )


@router.post("/insights/{key}/feedback", response_model=FeedbackOut)
def give_feedback(key: InsightKey, body: FeedbackIn, customer: CurrentCustomer, db: DbSession) -> FeedbackOut:
    data, insight = load_insight(db, customer, key)
    if insight.saving is not None and body.response != "dismissed":
        raise HTTPException(status_code=422, detail="You can dismiss a saving insight, or connect it to a goal.")
    if body.response == "wrong_category":
        s = insight.spending
        if s is None or body.corrected_category is None:
            raise HTTPException(status_code=422, detail="Choose the category these payments belong to.")
        if body.corrected_category == s.category:
            raise HTTPException(status_code=422, detail="Choose a different category.")
        ids = [t.id for t in services.spending_transactions(data, s)]
        repo.set_category_override(db, customer.id, ids, body.corrected_category)
    repo.upsert_feedback(db, customer.id, key, body.response)
    db.commit()
    return FeedbackOut(key=key, response=body.response)


@router.get("/insights/{key}/scenario", response_model=ScenarioResponseOut)
def scenario(
    key: InsightKey,
    customer: CurrentCustomer,
    db: DbSession,
    months: Annotated[int, Query(ge=1, le=MAX_FORECAST_MONTHS)] = 3,
) -> ScenarioResponseOut:
    data, insight = load_insight(db, customer, key)
    s = insight.spending
    if s is None:
        raise HTTPException(status_code=404, detail="There's no scenario for this insight.")
    inputs = services.forecast_inputs(data)
    one_off, continues = compare(inputs, s.category, s.amount, s.baseline.typical, months, add_months(s.month, 1))
    return ScenarioResponseOut(
        key=key,
        months=months,
        cash_buffer_cents=inputs.cash_buffer,
        one_off=_scenario_out(one_off),
        continues=_scenario_out(continues),
        assumptions=forecast_assumptions(inputs, s),
        coverage_note=COVERAGE_NOTE,
    )
