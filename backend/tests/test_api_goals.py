import pytest

from app.models import Goal
from tests.helpers import login

SAVING = "saving:2026-09"
FOOD = "spend:food:2026-09"
JEAN_SAVINGS = 2_526_552


def car(**overrides):
    body = {"kind": "car", "name": "New car", "target_cents": 1_500_000, "earmarked_cents": 300_000, "monthly_contribution_cents": 45_000}
    body.update(overrides)
    return body


def test_create_goal_from_saving_insight(client, seeded):
    login(client, "jean")
    response = client.post("/api/goals", json=car(from_insight=SAVING))
    assert response.status_code == 201, response.text
    goal = response.json()
    assert goal["plan"]["months_needed"] == 27
    assert goal["plan"]["estimated_completion"] == "2028-12-01"
    assert goal["plan"]["progress_pct"] == 20
    assert [s["title"] for s in goal["next_steps"]] == ["Set up a monthly savings plan", "Compare car financing (illustrative)"]
    assert client.get("/api/overview").json()["insights"] == []  # the insight is now connected


def test_list_goals(client, seeded):
    login(client, "jean")
    client.post("/api/goals", json=car())
    body = client.get("/api/goals").json()
    assert len(body["goals"]) == 1
    assert body["available_to_earmark_cents"] == JEAN_SAVINGS - 300_000
    assert body["suggested_monthly_cents"] == 45_000
    assert "verified" in body["verify_note"]


def test_target_date_gives_required_monthly(client, seeded):
    login(client, "jean")
    goal = client.post("/api/goals", json=car(target_date="2027-12-31")).json()
    assert goal["plan"]["required_monthly_cents"] == 80_000
    assert goal["plan"]["on_track"] is False


def test_other_customers_goal_is_not_found(client, db, seeded):
    login(client, "desmet")
    goal_id = client.post("/api/goals", json=car(earmarked_cents=0)).json()["id"]
    login(client, "jean")
    assert client.get(f"/api/goals/{goal_id}").status_code == 404
    assert client.patch(f"/api/goals/{goal_id}", json={"name": "Mine now"}).status_code == 404
    assert client.delete(f"/api/goals/{goal_id}").status_code == 404
    assert client.post("/api/goals/estimate", json={**car(), "goal_id": goal_id}).status_code == 404
    db.expire_all()
    assert db.get(Goal, goal_id).name == "New car"


def test_earmark_cannot_exceed_savings(client, seeded):
    login(client, "jean")
    response = client.post("/api/goals", json=car(target_cents=500_000_000, earmarked_cents=JEAN_SAVINGS + 1))
    assert response.status_code == 422
    assert "earmark at most" in response.json()["detail"]


def test_earmark_cannot_exceed_target(client, seeded):
    login(client, "jean")
    assert client.post("/api/goals", json=car(target_cents=100_000, earmarked_cents=200_000)).status_code == 422


def test_earmarks_add_up_across_goals(client, seeded):
    login(client, "jean")
    assert client.post("/api/goals", json=car(target_cents=5_000_000, earmarked_cents=2_000_000)).status_code == 201
    assert client.post("/api/goals", json=car(target_cents=5_000_000, earmarked_cents=600_000)).status_code == 422


def test_edit_goal_earmark_excludes_itself(client, seeded):
    login(client, "jean")
    goal_id = client.post("/api/goals", json=car(target_cents=5_000_000, earmarked_cents=2_000_000)).json()["id"]
    response = client.patch(f"/api/goals/{goal_id}", json={"earmarked_cents": 2_500_000})
    assert response.status_code == 200
    assert response.json()["earmarked_cents"] == 2_500_000


@pytest.mark.parametrize(
    "overrides",
    [
        {"target_cents": 0},
        {"target_cents": 1_000_000_001},
        {"monthly_contribution_cents": -1},
        {"monthly_contribution_cents": 10_000_001},
        {"name": "   "},
        {"name": "x" * 61},
        {"kind": "yacht"},
        {"target_date": "2026-09-30"},
        {"target_date": "2080-01-01"},
        {"customer_id": 1},
    ],
)
def test_invalid_goals_are_rejected(client, seeded, overrides):
    login(client, "jean")
    assert client.post("/api/goals", json=car(**overrides)).status_code == 422
    assert client.get("/api/goals").json()["goals"] == []


def test_patch_rejects_null_for_required_fields_but_can_clear_the_date(client, seeded):
    login(client, "jean")
    goal_id = client.post("/api/goals", json=car(target_date="2027-12-31")).json()["id"]
    assert client.patch(f"/api/goals/{goal_id}", json={"name": None}).status_code == 422
    assert client.patch(f"/api/goals/{goal_id}", json={"target_cents": None}).status_code == 422
    cleared = client.patch(f"/api/goals/{goal_id}", json={"target_date": None})
    assert cleared.status_code == 200 and cleared.json()["target_date"] is None


def test_from_insight_must_be_this_customers_saving_insight(client, seeded):
    login(client, "desmet")
    assert client.post("/api/goals", json=car(earmarked_cents=0, from_insight=SAVING)).status_code == 404
    assert client.post("/api/goals", json=car(earmarked_cents=0, from_insight=FOOD)).status_code == 422
    login(client, "jean")
    assert client.post("/api/goals", json=car(from_insight=FOOD)).status_code == 404
    assert client.post("/api/goals", json=car(from_insight="saving:bad")).status_code == 422


def test_estimate_does_not_save(client, seeded):
    login(client, "jean")
    response = client.post("/api/goals/estimate", json=car())
    assert response.status_code == 200
    assert response.json()["plan"]["months_needed"] == 27
    assert client.get("/api/goals").json()["goals"] == []


def test_delete_own_goal(client, seeded):
    login(client, "jean")
    goal_id = client.post("/api/goals", json=car()).json()["id"]
    assert client.delete(f"/api/goals/{goal_id}").status_code == 204
    assert client.get(f"/api/goals/{goal_id}").status_code == 404


def test_huge_goal_id_is_rejected_cleanly(client, seeded):
    login(client, "jean")
    assert client.get("/api/goals/99999999999999999999").status_code == 422
    assert client.get("/api/goals/0").status_code == 422


def test_goals_require_login(client, seeded):
    assert client.get("/api/goals").status_code == 401
    assert client.post("/api/goals", json=car()).status_code == 401


def test_other_customer_cannot_touch_goal_and_gets_identical_404(client, db, seeded):
    login(client, "desmet")
    goal_id = client.post("/api/goals", json=car(earmarked_cents=0)).json()["id"]
    login(client, "jean")
    missing = client.get("/api/goals/2000000")
    for response in (
        client.get(f"/api/goals/{goal_id}"),
        client.patch(f"/api/goals/{goal_id}", json={"name": "Mine now", "earmarked_cents": 1}),
        client.delete(f"/api/goals/{goal_id}"),
    ):
        assert response.status_code == 404
        assert response.json() == missing.json() == {"detail": "Goal not found."}
    db.expire_all()
    goal = db.get(Goal, goal_id)
    assert goal is not None and goal.name == "New car" and goal.earmarked_cents == 0
    login(client, "desmet")
    assert client.get(f"/api/goals/{goal_id}").status_code == 200


def test_earmark_limit_is_per_customer(client, seeded):
    login(client, "jean")
    assert client.post("/api/goals", json=car(target_cents=5_000_000, earmarked_cents=JEAN_SAVINGS)).status_code == 201
    login(client, "desmet")
    body = client.get("/api/goals").json()
    assert body["goals"] == []
    assert body["available_to_earmark_cents"] > 0
    assert client.post("/api/goals", json=car(target_cents=5_000_000, earmarked_cents=1_000)).status_code == 201
