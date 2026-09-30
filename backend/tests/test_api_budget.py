from tests.helpers import add_customer, login

FOOD = "spend:food:2026-09"


def budget(client) -> dict:
    response = client.get("/api/budget")
    assert response.status_code == 200, response.text
    return response.json()


def by_category(body: dict) -> dict[str, dict]:
    return {c["category"]: c for c in body["categories"]}


def test_budget_requires_login(client, seeded):
    assert client.get("/api/budget").status_code == 401


def test_desmet_budget(client, seeded):
    login(client, "desmet")
    body = budget(client)
    assert body["month"] == "2026-09"
    assert (body["total_cents"], body["typical_total_cents"], body["status"]) == (718_087, 553_372, "above")
    assert body["note"] == "You spent €1,647 more than in a usual month."
    assert [c["category"] for c in body["categories"][:6]] == [
        "food", "healthcare", "children_education", "clothing", "leisure_culture", "housing_energy",
    ]
    food = body["categories"][0]
    assert food["label"] == "Groceries" and food["status"] == "high"
    assert (food["amount_cents"], food["typical_cents"], food["usual_low_cents"], food["usual_high_cents"]) == (
        142_000, 90_364, 84_201, 98_129,
    )
    assert food["insight_key"] == FOOD and food["noted"] is False
    assert [h["month"] for h in food["history"]] == ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]
    assert food["history"][-1]["amount_cents"] == 142_000
    # Seasonal back-to-school rise is orange, never red, and has no insight to open.
    school = by_category(body)["children_education"]
    assert school["status"] == "above" and school["insight_key"] is None
    assert "coverage_note" in body and "other banks" in body["coverage_note"]


def test_jean_budget_is_all_ok(client, seeded):
    login(client, "jean")
    body = budget(client)
    assert {c["status"] for c in body["categories"]} == {"ok"}
    assert body["status"] == "ok" and body["note"] == "In line with your usual month."


def test_dismissed_insight_is_no_longer_high(client, seeded):
    login(client, "desmet")
    assert client.post(f"/api/insights/{FOOD}/feedback", json={"response": "dismissed"}).status_code == 200
    food = by_category(budget(client))["food"]
    assert food["status"] == "above" and food["insight_key"] is None


def test_ongoing_insight_is_noted(client, seeded):
    login(client, "desmet")
    client.post(f"/api/insights/{FOOD}/feedback", json={"response": "ongoing"})
    food = by_category(budget(client))["food"]
    assert food["status"] == "high" and food["noted"] is True


def test_customer_without_transactions_gets_empty_budget(client, db, seeded):
    add_customer(db, "dora")
    login(client, "dora")
    body = budget(client)
    assert body["categories"] == [] and body["total_cents"] == 0 and body["status"] == "ok"
    assert body["month"] == "2026-09"
    assert "three full months" in body["note"]


def test_budget_ignores_query_params(client, seeded):
    """There is no way to ask for another customer's budget."""
    login(client, "jean")
    mine = budget(client)
    assert client.get("/api/budget?customer_id=2&username=desmet").json() == mine
