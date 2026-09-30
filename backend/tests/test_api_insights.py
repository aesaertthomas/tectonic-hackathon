import pytest
from sqlalchemy import func, select

from app import repo
from app.models import Transaction
from tests.helpers import add_customer, get_customer, login

FOOD = "spend:food:2026-09"
HEALTH = "spend:healthcare:2026-09"
SAVING = "saving:2026-09"


def overview_keys(client) -> list[str]:
    return [card["key"] for card in client.get("/api/overview").json()["insights"]]


def test_overview_requires_login(client, seeded):
    assert client.get("/api/overview").status_code == 401


def test_desmet_overview(client, seeded):
    login(client, "desmet")
    body = client.get("/api/overview").json()
    assert body["display_name"] == "Sophie & Thomas"
    assert body["as_of"] == "2026-09-30"
    assert [a["type"] for a in body["accounts"]] == ["current", "savings", "credit_card"]
    assert body["accounts"][0]["balance_cents"] == 93_539
    assert [c["key"] for c in body["insights"]] == [FOOD, HEALTH]
    assert body["insights"][0]["type"] == "spending" and body["insights"][0]["noted"] is False
    assert "other banks" in body["coverage_note"]


def test_lucas_overview_has_no_insights(client, seeded):
    login(client, "lucas")
    assert overview_keys(client) == []


def test_customer_without_transactions(client, db, seeded):
    add_customer(db, "dora")
    login(client, "dora")
    body = client.get("/api/overview").json()
    assert body["insights"] == [] and body["accounts"] == []
    assert client.get(f"/api/insights/{FOOD}").status_code == 404


def test_spending_detail(client, seeded):
    login(client, "desmet")
    body = client.get(f"/api/insights/{FOOD}").json()
    assert body["type"] == "spending" and body["category"] == "food"
    assert [h["month"] for h in body["history"]] == ["2026-03", "2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]
    assert body["history"][-1]["amount_cents"] == body["this_month_cents"] == 142_000
    assert (body["usual_low_cents"], body["usual_high_cents"], body["typical_cents"]) == (84_201, 98_129, 90_364)
    assert body["transactions"] and all(t["category"] == "food" for t in body["transactions"])
    assert sum(t["amount_cents"] for t in body["transactions"]) == -142_000
    assert body["evidence"] and body["feedback"] is None
    assert "food" not in [o["value"] for o in body["category_options"]]


def test_saving_detail(client, seeded):
    login(client, "jean")
    body = client.get(f"/api/insights/{SAVING}").json()
    assert body["type"] == "saving" and body["category"] is None
    assert len(body["history"]) == 12
    assert (body["typical_cents"], body["this_month_cents"]) == (20_000, 45_000)
    assert body["transactions"]


def test_another_customers_insight_is_not_found(client, seeded):
    login(client, "jean")
    assert client.get(f"/api/insights/{FOOD}").status_code == 404
    assert client.post(f"/api/insights/{FOOD}/feedback", json={"response": "dismissed"}).status_code == 404
    assert client.get(f"/api/insights/{FOOD}/scenario").status_code == 404
    login(client, "desmet")
    assert client.get(f"/api/insights/{SAVING}").status_code == 404


@pytest.mark.parametrize("key", ["not-a-key", "spend:food:2026-9", "spend:FOOD:2026-09", "saving:2026-09x"])
def test_malformed_key_is_rejected(client, seeded, key):
    login(client, "desmet")
    assert client.get(f"/api/insights/{key}").status_code == 422


def test_one_off_hides_the_insight(client, seeded):
    login(client, "desmet")
    response = client.post(f"/api/insights/{FOOD}/feedback", json={"response": "one_off"})
    assert response.status_code == 200 and response.json() == {"key": FOOD, "response": "one_off"}
    assert overview_keys(client) == [HEALTH]


def test_ongoing_keeps_it_and_marks_it_noted(client, seeded):
    login(client, "desmet")
    client.post(f"/api/insights/{FOOD}/feedback", json={"response": "ongoing"})
    cards = client.get("/api/overview").json()["insights"]
    assert cards[0]["key"] == FOOD and cards[0]["noted"] is True
    assert client.get(f"/api/insights/{FOOD}").json()["feedback"] == "ongoing"


def test_feedback_twice_is_idempotent(client, seeded):
    login(client, "desmet")
    assert client.post(f"/api/insights/{FOOD}/feedback", json={"response": "ongoing"}).status_code == 200
    assert client.post(f"/api/insights/{FOOD}/feedback", json={"response": "ongoing"}).status_code == 200
    assert client.post(f"/api/insights/{FOOD}/feedback", json={"response": "dismissed"}).status_code == 200
    assert overview_keys(client) == [HEALTH]


def test_wrong_category_moves_the_transactions(client, db, seeded):
    login(client, "desmet")
    response = client.post(
        f"/api/insights/{FOOD}/feedback", json={"response": "wrong_category", "corrected_category": "household_maintenance"}
    )
    assert response.status_code == 200
    keys = overview_keys(client)
    assert FOOD not in keys and HEALTH in keys
    # Correct behaviour: the moved €1,420 now makes the corrected category stand out instead.
    assert "spend:household_maintenance:2026-09" in keys
    assert client.get(f"/api/insights/{FOOD}").status_code == 404  # September groceries are no longer high
    db.expire_all()
    moved = db.scalar(
        select(func.count()).select_from(Transaction).where(
            Transaction.customer_id == get_customer(db, "desmet").id,
            Transaction.category_override == "household_maintenance",
        )
    )
    assert moved > 0


@pytest.mark.parametrize(
    "body",
    [
        {"response": "wrong_category"},
        {"response": "wrong_category", "corrected_category": "food"},
        {"response": "wrong_category", "corrected_category": "salary"},
        {"response": "one_off", "corrected_category": "clothing"},
        {"response": "goal_created"},
        {"response": "one_off", "extra": 1},
    ],
)
def test_invalid_feedback_is_rejected(client, seeded, body):
    login(client, "desmet")
    assert client.post(f"/api/insights/{FOOD}/feedback", json=body).status_code == 422
    assert overview_keys(client) == [FOOD, HEALTH]


def test_saving_insight_only_accepts_dismiss(client, seeded):
    login(client, "jean")
    assert client.post(f"/api/insights/{SAVING}/feedback", json={"response": "one_off"}).status_code == 422
    assert client.post(f"/api/insights/{SAVING}/feedback", json={"response": "dismissed"}).status_code == 200
    assert overview_keys(client) == []


def test_scenario(client, seeded):
    login(client, "desmet")
    body = client.get(f"/api/insights/{FOOD}/scenario?months=3").json()
    assert body["months"] == 3 and body["cash_buffer_cents"] == 100_000
    assert [m["month"] for m in body["one_off"]["months"]] == ["2026-10", "2026-11", "2026-12"]
    assert [m["end_balance_cents"] for m in body["one_off"]["months"]] == [130_167, 166_795, 322_423]
    assert [m["end_balance_cents"] for m in body["continues"]["months"]] == [78_531, 63_523, 167_515]
    assert body["continues"]["savings_transfer_may_be_needed"] is True
    assert body["one_off"]["savings_transfer_may_be_needed"] is False
    lines = body["continues"]["months"][0]["lines"]
    assert any(line["confirmed"] for line in lines) and any(not line["confirmed"] for line in lines)
    assert lines[-1]["label"] == "Extra grocery spending"
    assert body["assumptions"]


@pytest.mark.parametrize("months", [0, 4, -1])
def test_scenario_months_out_of_range(client, seeded, months):
    login(client, "desmet")
    assert client.get(f"/api/insights/{FOOD}/scenario?months={months}").status_code == 422


def test_saving_insight_has_no_scenario(client, seeded):
    login(client, "jean")
    assert client.get(f"/api/insights/{SAVING}/scenario").status_code == 404


def test_feedback_lost_insert_race_updates_the_existing_row(db, session_factory, seeded):
    customer_id = get_customer(db, "desmet").id
    racing = session_factory()
    repo.upsert_feedback(racing, customer_id, FOOD, "ongoing")
    racing.commit()
    racing.close()
    real_scalar, misses = db.scalar, [None]  # first lookup misses, as if the other request had not committed yet
    db.scalar = lambda *a, **k: misses.pop() if misses else real_scalar(*a, **k)
    repo.upsert_feedback(db, customer_id, FOOD, "dismissed")
    db.commit()
    db.expire_all()
    assert repo.feedback_map(db, customer_id) == {FOOD: "dismissed"}


def test_other_customers_feedback_cannot_be_read_or_overwritten(client, db, seeded):
    login(client, "desmet")
    assert client.post(f"/api/insights/{FOOD}/feedback", json={"response": "ongoing"}).status_code == 200
    login(client, "lucas")
    response = client.post(f"/api/insights/{FOOD}/feedback", json={"response": "one_off"})
    assert response.status_code == 404 and response.json()["detail"] == "Insight not found."
    assert client.get(f"/api/insights/{FOOD}").json()["detail"] == "Insight not found."
    login(client, "desmet")
    assert client.get(f"/api/insights/{FOOD}").json()["feedback"] == "ongoing"
    assert FOOD in overview_keys(client)


def test_wrong_category_never_moves_another_customers_transactions(client, db, seeded):
    login(client, "lucas")
    client.post(f"/api/insights/{FOOD}/feedback", json={"response": "wrong_category", "corrected_category": "clothing"})
    assert db.scalar(select(func.count()).select_from(Transaction).where(Transaction.category_override.is_not(None))) == 0
