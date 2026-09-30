from datetime import date

from app.engine.budget import CategoryBudget, category_budgets, spend_status
from app.engine.texts import budget_note, month_note
from app.engine.types import Kind
from tests.factories import MAR, SEP, monthly

JUN = date(2026, 6, 1)


# --- status ------------------------------------------------------------------------------------

def test_flagged_is_high_regardless_of_amount():
    assert spend_status(100, 1_000, flagged=True) == "high"


def test_more_than_ten_percent_above_is_above():
    assert spend_status(11_001, 10_000) == "above"


def test_exactly_ten_percent_above_is_ok():
    assert spend_status(11_000, 10_000) == "ok"


def test_zero_typical_with_spending_is_above():
    assert spend_status(500, 0) == "above"


def test_negative_amount_is_ok():
    assert spend_status(-2_000, 5_000) == "ok"


# --- category_budgets -------------------------------------------------------------------------

def test_sorted_by_status_then_amount():
    txns = (
        monthly(MAR, [300, 300, 300, 300, 300, 300, 600], "food")
        + monthly(MAR, [100, 100, 100, 100, 100, 100, 150], "clothing")
        + monthly(MAR, [900, 900, 900, 900, 900, 900, 900], "housing_energy")
        + monthly(MAR, [50, 50, 50, 50, 50, 50, 50], "communication")
    )
    found = category_budgets(txns, SEP, MAR, flagged={"food"})
    assert [(b.category, b.status) for b in found] == [
        ("food", "high"),
        ("clothing", "above"),
        ("housing_energy", "ok"),
        ("communication", "ok"),
    ]
    food = found[0]
    assert (food.amount, food.typical, food.low, food.high) == (60_000, 30_000, 30_000, 30_000)


def test_history_is_last_six_months_ending_at_analysis_month():
    txns = monthly(MAR, [1, 2, 3, 4, 5, 6, 7], "food")
    [food] = category_budgets(txns, SEP, MAR, flagged=())
    assert [m for m, _ in food.history] == [date(2026, m, 1) for m in (4, 5, 6, 7, 8, 9)]
    assert [a for _, a in food.history] == [200, 300, 400, 500, 600, 700]


def test_history_never_starts_before_first_full_month():
    txns = monthly(JUN, [10, 10, 10, 10], "food")
    [food] = category_budgets(txns, SEP, JUN, flagged=())
    assert [m for m, _ in food.history] == [date(2026, m, 1) for m in (6, 7, 8, 9)]


def test_skips_categories_without_spending():
    txns = monthly(MAR, [0, 0, 0, 0, 0, 0, 0], "clothing") + monthly(MAR, [10] * 7, "food")
    assert [b.category for b in category_budgets(txns, SEP, MAR, flagged=())] == ["food"]


def test_needs_three_baseline_months():
    txns = monthly(JUN, [10, 10, 10, 10], "food")
    # With first full month July, Sep's baseline is Jul–Aug: only 2 months.
    assert category_budgets(txns, SEP, date(2026, 7, 1), flagged=()) == []


def test_refund_month_does_not_crash():
    txns = monthly(MAR, [100, 100, 100, 100, 100, 100], "leisure_culture") + monthly(
        SEP, [50], "leisure_culture", kind=Kind.REFUND, sign=1
    )
    [leisure] = category_budgets(txns, SEP, MAR, flagged=())
    assert leisure.amount == -5_000 and leisure.status == "ok"


# --- notes ------------------------------------------------------------------------------------

def budget(amount: int, typical: int, status: str, low: int = 0, high: int = 0) -> CategoryBudget:
    return CategoryBudget("food", amount, typical, low, high, (), status)  # type: ignore[arg-type]


def test_high_note_names_the_usual_range():
    assert budget_note(budget(142_000, 90_364, "high", 84_201, 98_129)) == (
        "€1,420 this month, above your usual range of €842–€981."
    )


def test_above_note_gives_the_difference():
    assert budget_note(budget(44_783, 25_861, "above")) == "€189 more than your usual month."


def test_clearly_below_note():
    assert budget_note(budget(29_595, 36_846, "ok")) == "€73 less than your usual month."


def test_in_line_note():
    assert budget_note(budget(9_858, 10_153, "ok")) == "In line with your usual month."


def test_negative_amount_is_ok_and_clamped_note():
    assert budget_note(budget(-5_000, 10_000, "ok")) == "€150 less than your usual month."


def test_month_note_above_below_in_line():
    assert month_note(718_087, 553_372) == "You spent €1,647 more than in a usual month."
    assert month_note(80_000, 100_000) == "You spent €200 less than in a usual month."
    assert month_note(176_823, 189_453) == "In line with your usual month."
