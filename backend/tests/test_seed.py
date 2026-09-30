from datetime import date, datetime

import pytest
from sqlalchemy import select

from app import repo, services
from app.engine.baseline import monthly_income, monthly_spend
from app.engine.forecast import compare
from app.engine.money import add_months
from app.engine.types import SPENDING_CATEGORIES
from app.models import Goal, Transaction
from app.security import verify_password
from app.seed import DEMO_PROFILES, import_dataset, to_cents
from tests.helpers import PASSWORD, get_customer

SEP = date(2026, 9, 1)


def _data(db, username):
    data = repo.load_customer_data(db, get_customer(db, username))
    assert data is not None
    return data


def test_to_cents_is_exact():
    assert to_cents(935.39) == 93_539
    assert to_cents(-682.84) == -68_284
    assert to_cents(13.99) == 1_399
    assert to_cents(2300) == 230_000


def test_engine_totals_match_the_dataset_summary(db, seeded, dataset):
    for profile in dataset["profiles"]:
        data = _data(db, DEMO_PROFILES[profile["id"]][0])
        income = monthly_income(data.txns)
        spend = {c: monthly_spend(data.txns, c) for c in SPENDING_CATEGORIES}
        for summary in profile["monthly_summary"]:
            month = date.fromisoformat(summary["month"] + "-01")
            assert abs(income.get(month, 0) - to_cents(summary["income_eur"])) <= 1, (profile["id"], summary["month"])
            for category in SPENDING_CATEGORIES:
                expected = to_cents(summary["spending_by_category_eur"].get(category, 0))
                assert abs(spend[category].get(month, 0) - expected) <= 1, (profile["id"], summary["month"], category)


def test_import_sets_as_of_accounts_and_balances(db, seeded):
    desmet = get_customer(db, "desmet")
    assert desmet.data_as_of == date(2026, 9, 30)
    assert desmet.display_name == "Sophie & Thomas"
    assert desmet.cash_buffer_cents == 100_000
    accounts = repo.accounts(db, desmet.id)
    assert [a.type for a in accounts] == ["current", "savings", "credit_card"]
    assert [a.balance_cents for a in accounts] == [93_539, 3_217_288, -68_284]
    data = _data(db, "desmet")
    assert data.analysis_month == SEP
    assert data.first_full_month == date(2024, 10, 1)


def test_desmet_insights(db, seeded):
    insights = services.all_insights(_data(db, "desmet"))
    assert [i.key for i in insights] == ["spend:food:2026-09", "spend:healthcare:2026-09"]
    food = insights[0].spending
    assert food is not None
    assert (food.amount, food.baseline.low, food.baseline.high, food.baseline.typical) == (142_000, 84_201, 98_129, 90_364)
    assert insights[0].headline == "Your grocery spending was €1,420 in September. Your usual range is €842–€981."


def test_jean_saving_insight(db, seeded):
    [insight] = services.all_insights(_data(db, "jean"))
    assert insight.key == "saving:2026-09"
    assert insight.saving is not None
    assert (insight.saving.basis, insight.saving.reference_typical, insight.saving.recent_typical) == ("year_ago", 20_000, 45_000)
    assert insight.headline == "You've increased your monthly saving contributions from around €200 to €450."


def test_lucas_has_no_insights(db, seeded):
    assert services.all_insights(_data(db, "lucas")) == []


def test_desmet_forecast(db, seeded):
    data = _data(db, "desmet")
    food = services.all_insights(data)[0].spending
    assert food is not None
    inputs = services.forecast_inputs(data)
    assert inputs.start_balance == 93_539
    one_off, continues = compare(inputs, "food", food.amount, food.baseline.typical, 3, add_months(SEP, 1))
    assert [m.end_balance for m in one_off.months] == [130_167, 166_795, 322_423]
    assert [m.end_balance for m in continues.months] == [78_531, 63_523, 167_515]
    assert not one_off.savings_transfer_may_be_needed
    assert continues.below_buffer and continues.savings_transfer_may_be_needed


def test_suggested_saving_and_typical_spending(db, seeded):
    assert services.suggested_monthly_saving(_data(db, "jean")) == 45_000
    assert services.suggested_monthly_saving(None) == 0
    assert services.typical_monthly_spending(_data(db, "desmet")) == 553_372


def test_passwords_are_hashed(db, seeded):
    customer = get_customer(db, "jean")
    assert customer.password_hash != PASSWORD
    assert verify_password(customer.password_hash, PASSWORD)
    assert seeded == {"jean": PASSWORD, "desmet": PASSWORD, "lucas": PASSWORD}


def test_random_passwords_when_none_given(db, dataset):
    credentials = import_dataset(db, dataset)
    assert len(set(credentials.values())) == 3
    assert all(len(pw) >= 16 for pw in credentials.values())


def test_unknown_spending_category_fails_loudly(db):
    bad = {
        "dataset": {"period": {"to": "2026-09"}},
        "profiles": [
            {
                "id": "X1",
                "name": "Test Person",
                "accounts": [{"id": "X1-CUR", "type": "current", "name": "Current"}],
                "monthly_summary": [{"closing_balances_eur": {"X1-CUR": 10}}],
                "recurring": [],
                "transactions": [
                    {"id": "T1", "date": "2026-09-01", "account_id": "X1-CUR", "amount": -5, "merchant": "M", "category": "gadgets", "type": "expense"}
                ],
            }
        ],
    }
    with pytest.raises(ValueError, match="gadgets"):
        import_dataset(db, bad, password="x")


def test_repo_is_scoped_by_customer(db, seeded):
    jean, desmet = get_customer(db, "jean"), get_customer(db, "desmet")
    goal = Goal(
        customer_id=desmet.id, kind="car", name="Car", target_cents=100, target_date=None,
        earmarked_cents=0, monthly_contribution_cents=0, created_at=datetime(2026, 9, 30),
    )
    db.add(goal)
    db.commit()
    assert repo.goal(db, jean.id, goal.id) is None
    assert repo.goal(db, desmet.id, goal.id) is not None
    assert repo.goals(db, jean.id) == []


def test_category_override_cannot_touch_another_customer(db, seeded):
    jean, desmet = get_customer(db, "jean"), get_customer(db, "desmet")
    desmet_txn = db.scalars(select(Transaction).where(Transaction.customer_id == desmet.id)).first()
    repo.set_category_override(db, jean.id, [desmet_txn.id], "other")
    db.commit()
    db.expire_all()
    assert db.get(Transaction, desmet_txn.id).category_override is None
