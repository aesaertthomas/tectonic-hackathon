from datetime import date

from app.engine.goals import GoalPlan, plan_goal
from app.engine.suggestions import VERIFY_NOTE, next_steps
from app.engine.types import GoalKind

AS_OF = date(2026, 9, 30)


def test_timeline_for_a_car():
    plan = plan_goal(target_cents=1_500_000, earmarked_cents=300_000, monthly_contribution_cents=45_000, target_date=None, as_of=AS_OF)
    assert plan == GoalPlan(
        remaining_cents=1_200_000,
        months_needed=27,
        estimated_completion=date(2028, 12, 1),
        required_monthly_cents=None,
        on_track=None,
        progress_pct=20,
    )


def test_target_date_gives_required_monthly_and_on_track():
    plan = plan_goal(target_cents=1_500_000, earmarked_cents=300_000, monthly_contribution_cents=45_000, target_date=date(2027, 12, 31), as_of=AS_OF)
    assert plan.required_monthly_cents == 80_000
    assert plan.on_track is False


def test_no_contribution_means_no_estimate():
    plan = plan_goal(target_cents=100_000, earmarked_cents=0, monthly_contribution_cents=0, target_date=None, as_of=AS_OF)
    assert plan.months_needed is None and plan.estimated_completion is None


def test_already_reached():
    plan = plan_goal(target_cents=100_000, earmarked_cents=100_000, monthly_contribution_cents=0, target_date=date(2027, 1, 31), as_of=AS_OF)
    assert (plan.remaining_cents, plan.months_needed, plan.progress_pct, plan.on_track) == (0, 0, 100, True)


def test_target_date_this_month_counts_as_one_month():
    plan = plan_goal(target_cents=100_000, earmarked_cents=0, monthly_contribution_cents=10_000, target_date=date(2026, 9, 30), as_of=AS_OF)
    assert plan.required_monthly_cents == 100_000


def test_next_steps_have_reasons_and_never_execute_products():
    car = next_steps(GoalKind.CAR, 0)
    assert [s.title for s in car] == ["Set up a monthly savings plan", "Compare car financing (illustrative)"]
    assert all(s.reason for s in car)
    home = next_steps(GoalKind.HOME, 0)
    assert any("doesn't establish mortgage affordability" in s.reason for s in home)
    emergency = next_steps(GoalKind.EMERGENCY, 235_000)
    assert "€7,050" in emergency[1].reason
    assert len(next_steps(GoalKind.OTHER, 0)) == 1
    assert "verified" in VERIFY_NOTE
