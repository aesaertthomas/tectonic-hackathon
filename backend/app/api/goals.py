from dataclasses import asdict
from datetime import date
from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Response
from sqlalchemy.orm import Session

from .. import repo, services
from ..deps import CurrentCustomer, DbSession
from ..engine.goals import plan_goal
from ..engine.money import fmt_eur
from ..engine.suggestions import VERIFY_NOTE, next_steps
from ..engine.types import GoalKind
from ..models import Goal
from ..schemas import GoalEstimateIn, GoalEstimateOut, GoalIn, GoalOut, GoalPatch, GoalPlanOut, GoalsOut, NextStepOut
from ..security import utcnow

router = APIRouter(prefix="/api", tags=["goals"])

GoalId = Annotated[int, Path(gt=0, le=2_147_483_647)]
GOAL_NOT_FOUND = "Goal not found."


def _check_target_date(target_date: date | None, as_of: date) -> None:
    if target_date is None:
        return
    latest = date(as_of.year + 50, as_of.month, min(as_of.day, 28))
    if not as_of < target_date <= latest:
        raise HTTPException(status_code=422, detail="Choose a target date in the future, within 50 years.")


def _check_earmark(db: Session, customer_id: int, earmarked: int, target: int, exclude_goal_id: int | None = None) -> None:
    if earmarked > target:
        raise HTTPException(status_code=422, detail="Earmarked savings can't be more than the target.")
    available = repo.savings_balance(db, customer_id) - repo.total_earmarked(db, customer_id, exclude_goal_id)
    if earmarked > available:
        raise HTTPException(status_code=422, detail=f"You can earmark at most {fmt_eur(max(0, available))} of your savings.")


def _plan_out(target: int, earmarked: int, monthly: int, target_date: date | None, as_of: date) -> GoalPlanOut:
    plan = plan_goal(
        target_cents=target, earmarked_cents=earmarked, monthly_contribution_cents=monthly, target_date=target_date, as_of=as_of
    )
    return GoalPlanOut(**asdict(plan))


def _steps_out(kind: GoalKind, spending: int) -> list[NextStepOut]:
    return [NextStepOut(title=s.title, reason=s.reason) for s in next_steps(kind, spending)]


def _goal_out(goal: Goal, as_of: date, spending: int) -> GoalOut:
    kind = GoalKind(goal.kind)
    return GoalOut(
        id=goal.id,
        kind=kind,
        name=goal.name,
        target_cents=goal.target_cents,
        target_date=goal.target_date,
        earmarked_cents=goal.earmarked_cents,
        monthly_contribution_cents=goal.monthly_contribution_cents,
        plan=_plan_out(goal.target_cents, goal.earmarked_cents, goal.monthly_contribution_cents, goal.target_date, as_of),
        next_steps=_steps_out(kind, spending),
    )


def _owned_goal(db: Session, customer_id: int, goal_id: int) -> Goal:
    goal = repo.goal(db, customer_id, goal_id)
    if goal is None:
        raise HTTPException(status_code=404, detail=GOAL_NOT_FOUND)
    return goal


@router.get("/goals", response_model=GoalsOut)
def list_goals(customer: CurrentCustomer, db: DbSession) -> GoalsOut:
    data = repo.load_customer_data(db, customer)
    spending = services.typical_monthly_spending(data)
    available = repo.savings_balance(db, customer.id) - repo.total_earmarked(db, customer.id)
    return GoalsOut(
        goals=[_goal_out(g, customer.data_as_of, spending) for g in repo.goals(db, customer.id)],
        available_to_earmark_cents=max(0, available),
        suggested_monthly_cents=services.suggested_monthly_saving(data),
        verify_note=VERIFY_NOTE,
    )


@router.post("/goals", status_code=201, response_model=GoalOut)
def create_goal(body: GoalIn, customer: CurrentCustomer, db: DbSession) -> GoalOut:
    _check_target_date(body.target_date, customer.data_as_of)
    _check_earmark(db, customer.id, body.earmarked_cents, body.target_cents)
    data = repo.load_customer_data(db, customer)
    if body.from_insight is not None:
        insight = services.find_insight(data, body.from_insight)
        if insight is None:
            raise HTTPException(status_code=404, detail="Insight not found.")
        if insight.type != "saving":
            raise HTTPException(status_code=422, detail="Only a saving insight can be connected to a goal.")
    goal = Goal(
        customer_id=customer.id,
        kind=body.kind.value,
        name=body.name,
        target_cents=body.target_cents,
        target_date=body.target_date,
        earmarked_cents=body.earmarked_cents,
        monthly_contribution_cents=body.monthly_contribution_cents,
        created_at=utcnow(),
    )
    db.add(goal)
    if body.from_insight is not None:
        repo.upsert_feedback(db, customer.id, body.from_insight, "goal_created")
    db.commit()
    return _goal_out(goal, customer.data_as_of, services.typical_monthly_spending(data))


@router.post("/goals/estimate", response_model=GoalEstimateOut)
def estimate_goal(body: GoalEstimateIn, customer: CurrentCustomer, db: DbSession) -> GoalEstimateOut:
    if body.goal_id is not None:
        _owned_goal(db, customer.id, body.goal_id)
    _check_target_date(body.target_date, customer.data_as_of)
    _check_earmark(db, customer.id, body.earmarked_cents, body.target_cents, exclude_goal_id=body.goal_id)
    data = repo.load_customer_data(db, customer)
    return GoalEstimateOut(
        plan=_plan_out(body.target_cents, body.earmarked_cents, body.monthly_contribution_cents, body.target_date, customer.data_as_of),
        next_steps=_steps_out(body.kind, services.typical_monthly_spending(data)),
        verify_note=VERIFY_NOTE,
    )


@router.get("/goals/{goal_id}", response_model=GoalOut)
def get_goal(goal_id: GoalId, customer: CurrentCustomer, db: DbSession) -> GoalOut:
    goal = _owned_goal(db, customer.id, goal_id)
    return _goal_out(goal, customer.data_as_of, services.typical_monthly_spending(repo.load_customer_data(db, customer)))


@router.patch("/goals/{goal_id}", response_model=GoalOut)
def update_goal(goal_id: GoalId, body: GoalPatch, customer: CurrentCustomer, db: DbSession) -> GoalOut:
    goal = _owned_goal(db, customer.id, goal_id)
    changes = body.model_dump(exclude_unset=True)
    if "target_date" in changes:
        _check_target_date(changes["target_date"], customer.data_as_of)
    _check_earmark(
        db,
        customer.id,
        changes.get("earmarked_cents", goal.earmarked_cents),
        changes.get("target_cents", goal.target_cents),
        exclude_goal_id=goal.id,
    )
    for field, value in changes.items():
        setattr(goal, field, value)
    db.commit()
    return _goal_out(goal, customer.data_as_of, services.typical_monthly_spending(repo.load_customer_data(db, customer)))


@router.delete("/goals/{goal_id}", status_code=204)
def delete_goal(goal_id: GoalId, customer: CurrentCustomer, db: DbSession) -> Response:
    goal = _owned_goal(db, customer.id, goal_id)
    db.delete(goal)
    db.commit()
    return Response(status_code=204)
