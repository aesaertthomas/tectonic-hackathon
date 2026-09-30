from datetime import date

from app.engine.detect import detect_saving_increase, detect_spending_increases
from app.engine.forecast import ForecastInputs
from app.engine.insights import compute_insights, visible_insights
from app.engine.texts import forecast_assumptions, saving_headline, spending_evidence, spending_headline
from app.engine.types import Kind
from tests.factories import MAR, SEP, item, monthly

JUL_2025 = date(2025, 7, 1)
SEP_2025 = date(2025, 9, 1)


def spending_txns():
    return monthly(SEP_2025, [921] + [900] * 5 + [981, 847, 874, 939, 842, 932] + [1420], "food")


def saving_txns():
    return monthly(JUL_2025, [200] * 8 + [300, 300] + [450] * 5, "transfer_to_savings", kind=Kind.INTERNAL_TRANSFER, account_id=2)


def test_spending_headline_matches_brief_wording():
    [s] = detect_spending_increases(spending_txns(), SEP, SEP_2025)
    assert spending_headline(s) == "Your grocery spending was €1,420 in September. Your usual range is €842–€981."


def test_spending_evidence_mentions_comparison_and_last_year():
    [s] = detect_spending_increases(spending_txns(), SEP, SEP_2025)
    evidence = spending_evidence(s)
    assert evidence[0] == "We compared September with your previous 6 months (March–August 2026)."
    assert any("Last September you spent €921" in line for line in evidence)


def test_saving_headline_matches_brief_wording():
    s = detect_saving_increase(saving_txns(), frozenset({2}), SEP, JUL_2025)
    assert s is not None
    assert saving_headline(s) == "You've increased your monthly saving contributions from around €200 to €450."


def test_compute_insights_orders_by_priority():
    txns = spending_txns() + saving_txns()
    insights = compute_insights(txns, frozenset({2}), SEP, JUL_2025)
    assert [i.key for i in insights] == ["saving:2026-09", "spend:food:2026-09"]  # 75,000 > 51,700
    assert insights[0].type == "saving" and insights[0].saving is not None
    assert insights[1].type == "spending" and insights[1].spending is not None


def test_feedback_hides_insights_except_ongoing():
    insights = compute_insights(spending_txns() + saving_txns(), frozenset({2}), SEP, JUL_2025)
    assert [i.key for i in visible_insights(insights, {"saving:2026-09": "goal_created"})] == ["spend:food:2026-09"]
    assert [i.key for i in visible_insights(insights, {"spend:food:2026-09": "ongoing"})] == ["saving:2026-09", "spend:food:2026-09"]
    for response in ("one_off", "wrong_category", "dismissed"):
        assert visible_insights(insights, {"spend:food:2026-09": response, "saving:2026-09": "dismissed"}) == []


def test_at_most_three_visible():
    txns = []
    for category in ("food", "clothing", "transport", "healthcare"):
        txns += monthly(MAR, [300, 300, 300, 300, 300, 300, 900], category)
    assert len(compute_insights(txns, frozenset(), SEP, MAR)) == 4
    assert len(visible_insights(compute_insights(txns, frozenset(), SEP, MAR), {})) == 3


def test_forecast_assumptions_state_limits():
    [s] = detect_spending_increases(spending_txns(), SEP, SEP_2025)
    inputs = ForecastInputs(0, 0, 100_000, (item("Salary", 5650, confirmed=False),), {"food": 90_364}, s.baseline.months)
    text = " ".join(forecast_assumptions(inputs, s))
    assert "Everything else stays the same." in text
    assert "Cash spending and other banks are not included." in text
    assert "€1,000" in text  # the cash buffer
