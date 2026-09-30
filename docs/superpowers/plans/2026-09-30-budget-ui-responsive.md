# Budget & Insights UI Refactor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the phone-in-a-browser frame with a responsive, desktop-first banking layout that matches `kbc-budget-inzichten.html`, and make the home screen a "Budget & insights" dashboard (category cards + expandable detail rows) fed by a new `GET /api/budget` endpoint.

**Architecture:** The backend gets one pure engine module (`engine/budget.py`) that compares each spending category's analysis-month total with the customer's usual month. The existing baseline code already computes that usual month. Status and sentence copy stay in the backend, the same as every other customer-facing text in this project. The API exposes it through a session-scoped endpoint with no ids in the URL. The frontend gets an app shell (fixed topbar, a sidebar that shrinks to icons, and a bottom tab bar on phones), a new design-token stylesheet copied from the mockup, and a rewritten `Home`. The other routes keep their logic and get only layout and CSS changes.

**Tech Stack:** FastAPI + Pydantic + pytest (backend), Vite + React 18 + TypeScript + react-router 6, plain CSS (frontend). No new dependencies.

**Spec:** `kbc-budget-inzichten.html` at the repo root is the visual reference. The decisions below come from the user (2026-09-30):
- Scope is **reskin + new home**. The shell and visual language apply to every screen, Home becomes the Budget dashboard, and the insight/scenario/goal flows stay and are restyled.
- The UI language is **English**. Borrow the mockup's layout and visuals, not its Dutch copy.
- **Not** in scope: the mockup's in-month weekly "spent so far + expected extra" chart, the month-switcher arrows, the search box, message/help tools. The demo's "today" is 30 Sep 2026, a completed month, so "so far vs expected" does not apply.

## Global Constraints

- Money is integer cents end to end. Format only in `frontend/src/format.ts` (frontend) or `fmt_eur` (backend sentences).
- Customer identity comes **only** from the session (`CurrentCustomer`). The new endpoint takes no customer or category id. This is an anti-IDOR rule and part of the Aikido score.
- Customer-facing sentences built from engine numbers live in `backend/app/engine/texts.py`. Calm, specific, no judgment.
- Red ("high") status is reserved for categories the detector flags **and** whose insight is still visible. Nothing else may render red.
- No horizontal page scroll at any width from 360px to 1920px.
- Colours, radii and fonts are copied from the mockup's `:root` and component rules. No new palette.
- No new npm or pip dependencies.
- The Makefile targets `make test` and `make build` must pass at the end of every task that touches their side.

## Review Focus

1. **Negative or zero month totals** (refunds bigger than spending, e.g. De Smet's leisure in Apr 2026 is −€219.51; categories with a usual month of €0). Expected: nothing crashes or divides by zero, bars clamp to 0–100% width, and the note still reads sensibly. Pinned in Task 1 (`test_zero_typical_with_spending_is_above`, `test_negative_amount_is_ok_and_clamped_note`) and Task 4 (`barWidth`).
2. **Feedback changes the dashboard.** After "Dismiss" or "One-off" on the grocery insight, groceries must stop being red and lose its insight link. After "Expected to continue" it stays red and shows "Noted". Pinned in Task 2 (`test_dismissed_insight_is_no_longer_high`, `test_ongoing_insight_is_noted`).
3. **Customer with no or too little history** (e.g. a freshly added customer). Expected: an empty-state message, not a 500 error and not an empty grid. Pinned in Task 2 (`test_customer_without_transactions_gets_empty_budget`) and rendered in Task 4.
4. **Phone widths (360–650px).** Expected: the sidebar is gone, a bottom tab bar reaches Budget and Goals, the Log out button can be reached, and the cards are 2-up. Checked in Task 3 and Task 6 with the browser width script.
5. **Long category names / big amounts** ("Insurance & bank fees", "€7,180.87"). Expected: they wrap inside the card and never overflow the grid cell. Checked in Task 4 step 6 and Task 6.

---

## File Structure

Backend:
- Create `backend/app/engine/budget.py`. It holds the per-category status and history for the analysis month. It is pure and does no I/O.
- Modify `backend/app/engine/texts.py` to add `budget_note`, `month_note` and `NO_HISTORY_NOTE`.
- Modify `backend/app/services.py` to add `flagged_categories`.
- Modify `backend/app/schemas.py` to add `BudgetCategoryOut` and `BudgetOut`.
- Create `backend/app/api/budget.py` with the `GET /api/budget` route.
- Modify `backend/app/main.py` to include the router.
- Create `backend/tests/test_engine_budget.py` and `backend/tests/test_api_budget.py`.

Frontend:
- Rewrite `frontend/src/styles.css` with the mockup tokens, base styles and shared components (card, buttons, fields, bars, chips).
- Create `frontend/src/shell.css` for the topbar, sidebar and bottom tabs, with responsive breakpoints.
- Create `frontend/src/routes/budget.css` for the dashboard-only styles.
- Create `frontend/src/components/Icons.tsx`, which holds the inline SVG icons from the mockup, the brand mark and the piggy illustration.
- Create `frontend/src/components/AppShell.tsx` for the topbar, sidebar and bottom tabs around the routes.
- Modify `frontend/src/components/Screen.tsx`. It becomes the page heading and content area inside the shell, with the same props.
- Modify `frontend/src/App.tsx` to drop the `.backdrop/.device` frame and wrap the routes in `AppShell`.
- Rewrite `frontend/src/routes/Home.tsx` as the Budget dashboard.
- Modify `frontend/src/routes/Login.tsx` so it becomes a centred card on the light background.
- Modify `frontend/src/routes/Insight.tsx`, `Scenario.tsx`, `Goals.tsx` and `GoalForm.tsx` to change wrappers and classes only, giving them two-column layouts on desktop.
- Modify `frontend/src/types.ts` to add the `Budget` types.
- Delete `frontend/src/assets/logo.svg`. It is replaced by the brand mark in `Icons.tsx`.

Docs: `PROJECT-INFO.md`, `README.md`.

---

### Task 1: Engine — per-category budget and notes

**Files:**
- Create: `backend/app/engine/budget.py`
- Modify: `backend/app/engine/texts.py` (append at end; add import)
- Test: `backend/tests/test_engine_budget.py`

**Interfaces:**
- Consumes: `baseline_months`, `baseline_for`, `monthly_spend`, `BASELINE_MIN_MONTHS` (`engine/baseline.py`); `add_months` (`engine/money.py`); `SPENDING_CATEGORIES`, `Txn` (`engine/types.py`); `fmt_eur` (`engine/money.py`).
- Produces:
  - `Status = Literal["high", "above", "ok"]`
  - `ABOVE_USUAL_PERCENT: int = 10`
  - `spend_status(amount: int, typical: int, flagged: bool = False) -> Status`
  - `@dataclass(frozen=True) CategoryBudget(category: str, amount: int, typical: int, low: int, high: int, history: tuple[tuple[date, int], ...], status: Status)`
  - `category_budgets(txns: Sequence[Txn], analysis_month: date, first_full: date, flagged: Collection[str]) -> list[CategoryBudget]` sorts by status (high, above, ok), then by amount descending, then by category.
  - `texts.budget_note(b: CategoryBudget) -> str`, `texts.month_note(total: int, typical: int) -> str`, `texts.NO_HISTORY_NOTE: str`

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_engine_budget.py`:

```python
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
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `cd backend && .venv/bin/pytest tests/test_engine_budget.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'app.engine.budget'`.

- [ ] **Step 3: Implement `engine/budget.py`**

```python
"""Each spending category's analysis-month total next to the customer's usual month."""

from collections.abc import Collection, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Literal

from .baseline import BASELINE_MIN_MONTHS, baseline_for, baseline_months, monthly_spend
from .money import add_months
from .types import SPENDING_CATEGORIES, Txn

Status = Literal["high", "above", "ok"]

ABOVE_USUAL_PERCENT = 10  # orange once a month is more than 10% above the usual month
HISTORY_MONTHS = 6
_ORDER: dict[Status, int] = {"high": 0, "above": 1, "ok": 2}


def spend_status(amount: int, typical: int, flagged: bool = False) -> Status:
    """Red only for detector-flagged categories; orange for a clear rise that isn't an insight."""
    if flagged:
        return "high"
    if amount * 100 > typical * (100 + ABOVE_USUAL_PERCENT):
        return "above"
    return "ok"


@dataclass(frozen=True)
class CategoryBudget:
    category: str
    amount: int
    typical: int
    low: int
    high: int
    history: tuple[tuple[date, int], ...]
    status: Status


def category_budgets(
    txns: Sequence[Txn], analysis_month: date, first_full: date, flagged: Collection[str]
) -> list[CategoryBudget]:
    months = baseline_months(analysis_month, first_full)
    if len(months) < BASELINE_MIN_MONTHS:
        return []
    chart = [add_months(analysis_month, -i) for i in range(HISTORY_MONTHS - 1, -1, -1)]
    found: list[CategoryBudget] = []
    for category in sorted(SPENDING_CATEGORIES):
        per_month = monthly_spend(txns, category)
        base = baseline_for(per_month, months)
        amount = per_month.get(analysis_month, 0)
        if base is None or (base.typical <= 0 and amount <= 0):
            continue
        found.append(
            CategoryBudget(
                category=category,
                amount=amount,
                typical=base.typical,
                low=base.low,
                high=base.high,
                history=tuple((m, per_month.get(m, 0)) for m in chart if m >= first_full),
                status=spend_status(amount, base.typical, category in flagged),
            )
        )
    return sorted(found, key=lambda b: (_ORDER[b.status], -b.amount, b.category))
```

- [ ] **Step 4: Add the notes to `engine/texts.py`**

Add `from .budget import ABOVE_USUAL_PERCENT, CategoryBudget` next to the existing imports, then append:

```python
NO_HISTORY_NOTE = "We need at least three full months of history before we can compare with your usual month."


def _clearly_below(amount: int, typical: int) -> bool:
    return amount * 100 < typical * (100 - ABOVE_USUAL_PERCENT)


def budget_note(b: CategoryBudget) -> str:
    if b.status == "high":
        return f"{fmt_eur(b.amount)} this month, above your usual range of {fmt_eur(b.low)}–{fmt_eur(b.high)}."
    if b.status == "above":
        return f"{fmt_eur(b.amount - b.typical)} more than your usual month."
    if _clearly_below(b.amount, b.typical):
        return f"{fmt_eur(b.typical - b.amount)} less than your usual month."
    return "In line with your usual month."


def month_note(total: int, typical: int) -> str:
    if total * 100 > typical * (100 + ABOVE_USUAL_PERCENT):
        return f"You spent {fmt_eur(total - typical)} more than in a usual month."
    if _clearly_below(total, typical):
        return f"You spent {fmt_eur(typical - total)} less than in a usual month."
    return "In line with your usual month."
```

- [ ] **Step 5: Run the tests and confirm they pass, then run the full suite**

Run: `cd backend && .venv/bin/pytest tests/test_engine_budget.py -q && .venv/bin/pytest -q`
Expected: all pass. A circular import error would mean `budget.py` imports `texts`, which it must not do.

- [ ] **Step 6: Commit**

```bash
git add backend/app/engine/budget.py backend/app/engine/texts.py backend/tests/test_engine_budget.py
git commit -m "feat(engine): per-category budget status and notes against the usual month"
```

---

### Task 2: API — `GET /api/budget`

**Files:**
- Modify: `backend/app/services.py` (add `flagged_categories`)
- Modify: `backend/app/schemas.py` (add `BudgetCategoryOut`, `BudgetOut`)
- Create: `backend/app/api/budget.py`
- Modify: `backend/app/main.py:7,22-25` (import + `include_router`)
- Test: `backend/tests/test_api_budget.py`

**Interfaces:**
- Consumes: Task 1's `category_budgets`, `spend_status`, `budget_note`, `month_note` and `NO_HISTORY_NOTE`. Also `visible_insights` (`engine/insights.py`), `all_insights` (`services.py`), `repo.load_customer_data` and `repo.feedback_map`, `category_name` (`engine/types.py`), `analysis_month` (`engine/baseline.py`), `month_key`, and `COVERAGE_NOTE`.
- Produces the JSON contract that Task 4 relies on:

```json
{
  "month": "2026-09",
  "total_cents": 718087,
  "typical_total_cents": 553372,
  "status": "above",
  "note": "You spent €1,647 more than in a usual month.",
  "categories": [
    {
      "category": "food", "label": "Groceries",
      "amount_cents": 142000, "typical_cents": 90364,
      "usual_low_cents": 84201, "usual_high_cents": 98129,
      "status": "high", "note": "…",
      "history": [{"month": "2026-04", "amount_cents": 87467}],
      "insight_key": "spend:food:2026-09", "noted": false
    }
  ],
  "coverage_note": "Based on your KBC accounts only. …"
}
```

- [ ] **Step 1: Write the failing tests**

`backend/tests/test_api_budget.py`:

```python
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
```

- [ ] **Step 2: Run the tests and confirm they fail**

Run: `cd backend && .venv/bin/pytest tests/test_api_budget.py -q`
Expected: FAIL with 404 on `/api/budget`. The first test fails because it gets 404, not 401.

- [ ] **Step 3: Add `flagged_categories` to `services.py`**

Add `visible_insights` to the existing `from .engine.insights import …` line, then append:

```python
def flagged_categories(data: CustomerData, feedback: dict[str, str]) -> dict[str, str]:
    """Category -> insight key, for spending insights the customer can still see."""
    return {
        i.spending.category: i.key
        for i in visible_insights(all_insights(data), feedback)
        if i.spending is not None
    }
```

- [ ] **Step 4: Add the schemas to `schemas.py`** (directly after `MonthAmountOut`, which they reference)

```python
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
```


- [ ] **Step 5: Create `api/budget.py`**

```python
from fastapi import APIRouter

from .. import repo, services
from ..deps import CurrentCustomer, DbSession
from ..engine.baseline import analysis_month
from ..engine.budget import category_budgets, spend_status
from ..engine.money import month_key
from ..engine.texts import COVERAGE_NOTE, NO_HISTORY_NOTE, budget_note, month_note
from ..engine.types import category_name
from ..schemas import BudgetCategoryOut, BudgetOut, MonthAmountOut

router = APIRouter(prefix="/api", tags=["budget"])


@router.get("/budget", response_model=BudgetOut)
def budget(customer: CurrentCustomer, db: DbSession) -> BudgetOut:
    data = repo.load_customer_data(db, customer)
    month = analysis_month(customer.data_as_of)
    feedback = repo.feedback_map(db, customer.id)
    flagged = services.flagged_categories(data, feedback) if data is not None else {}
    budgets = category_budgets(data.txns, data.analysis_month, data.first_full_month, flagged) if data is not None else []
    if not budgets:
        return BudgetOut(
            month=month_key(month), total_cents=0, typical_total_cents=0, status="ok",
            note=NO_HISTORY_NOTE, categories=[], coverage_note=COVERAGE_NOTE,
        )
    total = sum(b.amount for b in budgets)
    typical = sum(b.typical for b in budgets)
    return BudgetOut(
        month=month_key(month),
        total_cents=total,
        typical_total_cents=typical,
        status=spend_status(total, typical),
        note=month_note(total, typical),
        categories=[
            BudgetCategoryOut(
                category=b.category,
                label=category_name(b.category),
                amount_cents=b.amount,
                typical_cents=b.typical,
                usual_low_cents=b.low,
                usual_high_cents=b.high,
                status=b.status,
                note=budget_note(b),
                history=[MonthAmountOut(month=month_key(m), amount_cents=a) for m, a in b.history],
                insight_key=flagged.get(b.category),
                noted=feedback.get(flagged.get(b.category, "")) == "ongoing",
            )
            for b in budgets
        ],
        coverage_note=COVERAGE_NOTE,
    )
```

- [ ] **Step 6: Register the router in `main.py`**

Change `from .api import auth, goals, insights, overview` to `from .api import auth, budget, goals, insights, overview`, and add `app.include_router(budget.router)` after `app.include_router(overview.router)`.

- [ ] **Step 7: Run the tests and confirm they pass, then run the full suite**

Run: `cd backend && .venv/bin/pytest tests/test_api_budget.py -q && .venv/bin/pytest -q`
Expected: all pass. If the `typical_total_cents` assertions fail, compare with `services.typical_monthly_spending(data)`. Both sum the per-category medians and must agree. That was probed on 2026-09-30: De Smet 553,372, Jean 189,453, Lucas 95,849.

- [ ] **Step 8: Commit**

```bash
git add backend/app/services.py backend/app/schemas.py backend/app/api/budget.py backend/app/main.py backend/tests/test_api_budget.py
git commit -m "feat(api): session-scoped budget endpoint with per-category status"
```

---

### Task 3: Responsive app shell, design tokens, login

This task replaces the phone frame and ships nothing else visible. Every existing screen must still work inside the new shell. A reviewer can approve the shell and reject the dashboard, or the other way round, so the two are separate tasks.

**Files:**
- Rewrite: `frontend/src/styles.css`
- Create: `frontend/src/shell.css`
- Create: `frontend/src/components/Icons.tsx`
- Create: `frontend/src/components/AppShell.tsx`
- Modify: `frontend/src/components/Screen.tsx`
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/routes/Login.tsx`
- Modify: `frontend/src/routes/Home.tsx` (only: remove the "Log out" `action` — logout moves to the shell)
- Delete: `frontend/src/assets/logo.svg`

**Interfaces:**
- Consumes: `useAuth()` → `{ me, logout }` (`src/auth.ts`).
- Produces:
  - `Icon` component: `<Icon name={IconName} className?: string />`, where `IconName = "home" | "wallet" | "arrow" | "pig" | "trend" | "budget" | "doc" | "gear" | "cart" | "fork" | "car" | "bag" | "house" | "heart" | "chevron"`
  - `BrandMark` (no props) and `Piggy` (`className?: string`) components
  - `AppShell({ children })`
  - `Screen({ title, subtitle?, back?, action?, children })`. The existing props are unchanged and `subtitle` is new.
  - CSS classes that later tasks use: `.card`, `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-ghost`, `.field`, `.bar` (with a child `span`), `.percent`, `.chip`, `.tag`, `.red`/`.orange`/`.green` colour scopes that set `--color`, `--bright`, `--pale`, `--colorwash` and `--strong`, `.tile-icon`, `.grid-2`, `.stack`, `.stack-tight`, `.row`, `.grow`, `.muted`, `.small`, `.pos`, `.neg`, `.error`, `.warning`, `.headline`, `.card-title`, `.card-link`, `.chevron`, `.amount`, `.estimate`, `.legend`, `.segmented`, `.list`, `table.balances`, `.chart`/`.bar-rect`/`.bar-hi`/`.chart-band`/`.chart-label`, and `.progress` (goal progress; kept name).

**Class-name collision to fix:** the mockup's `.bar` is an HTML progress track, but `BarChart.tsx` uses `className="bar"` on SVG `<rect>`s. Rename the SVG classes in `BarChart.tsx` to `bar-rect` / `bar-rect bar-hi` in this task so the new `.bar` rule doesn't style the chart.

- [ ] **Step 1: Write `Icons.tsx`**

Copy the paths verbatim from the mockup (`kbc-budget-inzichten.html`). All stroke icons share the same `<svg>` attributes.

```tsx
const PATHS = {
  home: <><path d="m3 10 9-7 9 7v10H3Z" /><path d="M9 20v-7h6v7" /></>,
  wallet: <><path d="M20 7H5a2 2 0 0 1 0-4h13v4M4 5v14a2 2 0 0 0 2 2h14V7" /><path d="M20 11h-6v5h6M16 13.5h.01" /></>,
  arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
  pig: <path d="M7 7a8 8 0 0 1 10 0l4 1v7l-3 1-1 4h-3v-3H9v3H6l-1-5-3-2V9h3l1-5 4 2M15 10h.01" />,
  trend: <path d="m3 17 6-6 4 4 8-10m-6 0h6v6" />,
  budget: <><rect x="3" y="13" width="4" height="8" rx="1" /><rect x="10" y="8" width="4" height="13" rx="1" /><rect x="17" y="3" width="4" height="18" rx="1" /></>,
  doc: <path d="M6 3h8l4 4v14H6Zm8 0v5h4M9 12h6m-6 4h6" />,
  gear: <><path d="m9 3-1 3-3 1-2 4 2 2v4l4 2 3-1 3 1 4-2v-4l2-2-2-4-3-1-1-3Z" /><circle cx="12" cy="11" r="3" /></>,
  cart: <><path d="M2 3h3l3 12h11l3-9H6" /><circle cx="9" cy="20" r="1" /><circle cx="18" cy="20" r="1" /></>,
  fork: <path d="M4 3v6c0 3 6 3 6 0V3M7 3v18M20 21V3c-5 2-5 10 0 10" />,
  car: <path d="m5 8 2-5h10l2 5M3 9h18v9H3Zm2 9v3m14-3v3M6 13h2m8 0h2" />,
  bag: <path d="M5 8h14l2 13H3ZM9 9V6a3 3 0 0 1 6 0v3" />,
  house: <><path d="m3 10 9-7 9 7v10H3Z" /><path d="M9 20v-7h6v7" /></>,
  heart: <path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10Z" />,
  chevron: <path d="m9 5 7 7-7 7" />,
};

export type IconName = keyof typeof PATHS;

export function Icon({ name, className = "" }: { name: IconName; className?: string }) {
  return (
    <svg className={`icon ${className}`} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      {PATHS[name]}
    </svg>
  );
}

export function BrandMark() {
  return (
    <svg className="brand-logo" viewBox="0 0 80 64" role="img" aria-label="KBC">
      <circle cx="40" cy="12" r="10" fill="currentColor" />
      <path d="M10 28Q40 20 70 25V34H10Z" fill="currentColor" />
      <text x="8" y="58" fill="#003b71" fontFamily="Arial,sans-serif" fontWeight="900" fontSize="33" letterSpacing="-2">KBC</text>
    </svg>
  );
}
```

`Piggy`: copy the full inner markup of the mockup's `<svg class="pig" viewBox="0 0 190 100">` (it's the only `class="pig"` in the file). Convert it to JSX by changing `stop-color` → `stopColor`, `stroke-width` → `strokeWidth`, `font-size` → `fontSize`, `text-anchor` → `textAnchor`, `stroke-linecap` → `strokeLinecap`. Rename the gradient ids to `piggy-blue`/`piggy-gold` and update the `url(#…)` references to match. Render it with `aria-hidden="true"` and `className={`pig ${className ?? ""}`}`.

The `heart` path is new because the mockup has no healthcare icon. It is used for healthcare in Task 4.

- [ ] **Step 2: Rewrite `styles.css`**

Start from the mockup's `:root`, `body`, `h1–h4` and `a` rules, plus its component rules for `.tile-icon`, `.bar`, `.bar>span`, `.percent`, `.red/.orange/.green` and `.primary`. Keep every existing class listed under **Produces**, restyled with the mockup's tokens:

```css
:root {
  --ink: #071b62; --muted: #526ca1; --blue: #008cff; --action: #0078ee; --line: #e1edf9;
  --bg: #edf5fb; --card: #fff; --positive: #008646; --negative: #d71937;
  --warn-bg: #fff8ed; --warn-text: #942f12; --radius: 12px;
  --side: 214px; --top: 64px; --tabs: 0px;
  color: var(--ink);
  font: 14px/1.45 "Segoe UI", Arial, system-ui, sans-serif;
  -webkit-font-smoothing: antialiased;
}
* { box-sizing: border-box; }
html, body, #root { margin: 0; min-height: 100%; }
body { background: var(--bg); }
h1, h2, h3, h4, p { margin: 0; }
a { color: inherit; text-decoration: none; }
button, input, select { font: inherit; color: inherit; }
a:focus-visible, button:focus-visible, summary:focus-visible { outline: 3px solid #0099ee; outline-offset: 3px; }
svg.icon { width: 21px; height: 21px; flex-shrink: 0; vertical-align: middle; }

.card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 18px; }
.btn { display: inline-flex; align-items: center; justify-content: center; gap: 10px; width: 100%; border: 0; border-radius: 9px; padding: 12px 17px; font-weight: 600; cursor: pointer; text-align: center; }
.btn-primary { background: var(--action); color: #fff; box-shadow: 0 3px 8px #0078ee15; }
.btn-primary:hover { background: #006ad7; }
.btn-secondary { background: linear-gradient(#fff, #e9f5ff); color: #007df0; border: 1px solid #cce6ff; }
.btn-ghost { background: none; color: #0065c9; }
.btn:disabled { opacity: .5; cursor: default; }
```

Then add these, all adapted from the mockup:
- `.tile-icon` (42px rounded square, `#e8f6ff` background, `#008dff` icon)
- `.bar` (`height: 14px; background: var(--pale, #e4edf6); border-radius: 20px; overflow: hidden; flex: 1; min-width: 0`), and `.bar > span` using the gradient `var(--color, #2eb780)` → `var(--bright, #52c990)`
- `.percent`
- the three colour scopes `.red`, `.orange` and `.green`, with values exactly as in the mockup lines `.red{--color:#ff4c5d;…}` etc.
- `.chip` (`background: #e2f3ff; color: #0085ff`)
- `.tag` (`color: #0085ff`)
- `.headline` (`font-size: 19px; font-weight: 650; letter-spacing: -.3px`)
- `.field input/select` (1px `var(--line)` border, 9px radius, `#fff` background, focus outline `#0099ee`)
- `.segmented` (a white pill group with a border; the pressed button uses a `#e2f3ff` background and `#0085ff` text)
- `.warning` (`background: var(--warn-bg); color: var(--warn-text); border-radius: 9px`)
- `.progress` (the goal progress bar; same look as `.bar`)
- SVG chart classes: `.bar-rect { fill: #dae5f2 } .bar-hi { fill: var(--color, var(--blue)) } .chart-band { fill: #0078ee12 } .chart-label { font-size: 10px; fill: #34578d }`

Carry `.stack`, `.stack-tight`, `.row`, `.grow`, `.grid-2`, `.list`, `table.balances`, `.estimate`, `.legend`, `.muted`, `.small`, `.pos`, `.neg`, `.error`, `.amount`, `.card-title`, `.card-link` and `.chevron` over from the current file unchanged, except that their colours move to the new variables (`--text` becomes `--ink`, `--navy` becomes `--ink`, `--cyan` becomes `--blue`). Delete `.backdrop`, `.device`, `.screen`, `.center`, `.topbar*`, `.icon-btn`, `.link-btn`, `.content`, `.section-title` and `.login*`. They move to `shell.css`, or are no longer used.

Add at the end:

```css
@media (max-width: 650px) { .grid-2 { grid-template-columns: 1fr; } }
@media (prefers-reduced-motion: reduce) { html { scroll-behavior: auto; } }
```

- [ ] **Step 3: Write `shell.css`**

```css
.topbar { height: var(--top); position: fixed; inset: 0 0 auto; z-index: 10; background: #ffffffef; border-bottom: 1px solid var(--line); display: flex; align-items: center; gap: 24px; padding: 0 30px; backdrop-filter: blur(16px); }
.brand { width: 160px; flex-shrink: 0; display: flex; }
.brand-logo { height: 48px; width: 60px; color: #009fe3; }
.profile { margin-left: auto; display: flex; align-items: center; gap: 10px; white-space: nowrap; }
.avatar { border-radius: 50%; background: #c6e6ff; color: #0077d6; width: 34px; height: 34px; display: grid; place-items: center; font-weight: 600; font-size: 13px; }
.logout { background: none; border: 1px solid var(--line); border-radius: 8px; padding: 6px 10px; color: #0065c9; cursor: pointer; font-size: 12px; }

.sidebar { position: fixed; inset: var(--top) auto 0 0; width: var(--side); background: #ffffffd9; border-right: 1px solid var(--line); padding: 21px 8px; display: flex; flex-direction: column; z-index: 9; overflow-y: auto; }
.nav { display: flex; align-items: center; gap: 13px; padding: 12px 17px; border-radius: 8px; color: #102b6c; font-size: 13px; margin: 1px 0; }
.nav .icon { width: 19px; height: 19px; color: #3155a0; }
.nav[aria-disabled="true"] { cursor: default; }
.nav.active { background: #e2f3ff; color: #0085ff; }
.nav.active .icon { color: #0097ff; }
.nav.settings { margin-top: auto; }

.tabs { display: none; }

.page { margin-left: var(--side); padding: calc(var(--top) + 22px) 25px calc(30px + var(--tabs)); min-height: 100vh; background: radial-gradient(ellipse at 65% 25%, #e6f3fd80, transparent 70%); }
.page-inner { max-width: 1400px; margin: 0 auto; display: flex; flex-direction: column; gap: 22px; }
.page-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 20px; flex-wrap: wrap; }
.page-heading h1 { font-size: 31px; letter-spacing: -1px; line-height: 1.2; font-weight: 700; }
.page-heading p { color: var(--muted); font-size: 13px; margin-top: 8px; max-width: 640px; }
.back { display: inline-flex; align-items: center; gap: 6px; color: #0065c9; font-size: 13px; margin-bottom: 6px; }
.back .icon { width: 16px; height: 16px; transform: rotate(180deg); }

.login-page { min-height: 100vh; display: grid; place-items: center; padding: 24px 16px; background: radial-gradient(ellipse at 65% 25%, #e6f3fd, transparent 70%), var(--bg); }
.login { width: 100%; max-width: 400px; display: flex; flex-direction: column; gap: 22px; }
.login h1 { font-size: 26px; letter-spacing: -.6px; }
.loading { min-height: 100vh; display: grid; place-items: center; color: var(--muted); }

@media (max-width: 1150px) {
  :root { --side: 180px; }
  .brand { width: 126px; }
  .nav { font-size: 12px; padding: 12px; gap: 10px; }
  .page { padding-left: 18px; padding-right: 18px; }
}
@media (max-width: 950px) {
  :root { --side: 74px; }
  .brand { width: 36px; }
  .topbar { gap: 15px; padding: 0 18px; }
  .nav { justify-content: center; }
  .nav > span { display: none; }
  .profile b { display: none; }
}
@media (max-width: 650px) {
  :root { --side: 0px; --top: 58px; --tabs: 64px; }
  .sidebar { display: none; }
  .brand-logo { height: 42px; width: 52px; }
  .page { padding: calc(var(--top) + 16px) 14px calc(20px + var(--tabs)); }
  .page-heading h1 { font-size: 26px; }
  .tabs { display: flex; position: fixed; inset: auto 0 0; height: var(--tabs); z-index: 10; background: #fffffff2; border-top: 1px solid var(--line); backdrop-filter: blur(16px); padding-bottom: env(safe-area-inset-bottom); }
  .tabs a { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 3px; font-size: 11px; color: #102b6c; }
  .tabs a.active { color: #0085ff; }
}
@media print { .topbar, .sidebar, .tabs { display: none; } .page { margin: 0; padding: 0; } }
```

- [ ] **Step 4: Write `AppShell.tsx`**

The only real destinations are Budget (`/`, including `/insights/*`) and Goals (`/goals*`). The other sidebar entries copy the mockup and are inert: a `<span>` with `aria-disabled="true"`, never a link to nowhere.

```tsx
import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../auth";
import "../shell.css";
import { BrandMark, Icon, type IconName } from "./Icons";

const INERT: [IconName, string][] = [
  ["home", "Overview"], ["wallet", "Accounts"], ["arrow", "Payments"], ["trend", "Investments"],
];

function initials(name: string) {
  return name.split(/[\s&]+/).filter(Boolean).map((w) => w[0]!.toUpperCase()).slice(0, 2).join("");
}

export function AppShell({ children }: { children: ReactNode }) {
  const { me, logout } = useAuth();
  const { pathname } = useLocation();
  const onGoals = pathname.startsWith("/goals");
  const links = [
    { to: "/", icon: "budget" as const, label: "Budget & insights", active: !onGoals },
    { to: "/goals", icon: "pig" as const, label: "Goals", active: onGoals },
  ];

  return (
    <>
      <header className="topbar">
        <Link className="brand" to="/" aria-label="Budget & insights"><BrandMark /></Link>
        <span className="profile">
          <span className="avatar" aria-hidden="true">{initials(me.display_name)}</span>
          <b>{me.display_name}</b>
          <button type="button" className="logout" onClick={logout}>Log out</button>
        </span>
      </header>
      <aside className="sidebar">
        <nav aria-label="Main navigation">
          {INERT.map(([icon, label]) => (
            <span key={label} className="nav" aria-disabled="true"><Icon name={icon} /><span>{label}</span></span>
          ))}
          {links.map((l) => (
            <Link key={l.to} to={l.to} className={`nav${l.active ? " active" : ""}`} aria-current={l.active ? "page" : undefined}>
              <Icon name={l.icon} /><span>{l.label}</span>
            </Link>
          ))}
        </nav>
        <span className="nav settings" aria-disabled="true"><Icon name="gear" /><span>Settings</span></span>
      </aside>
      <nav className="tabs" aria-label="Main navigation">
        {links.map((l) => (
          <Link key={l.to} to={l.to} className={l.active ? "active" : undefined} aria-current={l.active ? "page" : undefined}>
            <Icon name={l.icon} /><span>{l.label}</span>
          </Link>
        ))}
      </nav>
      <main className="page"><div className="page-inner">{children}</div></main>
    </>
  );
}
```

`logout()` sets `me` to null, which renders `<Login>`, so no navigate is needed. On the next login, the URL is still whatever it was. That matches the current behaviour on 401.

- [ ] **Step 5: Rewrite `Screen.tsx`** (same call sites keep working)

```tsx
import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Icon } from "./Icons";

type Props = { title: string; subtitle?: string; back?: string; action?: ReactNode; children: ReactNode };

export function Screen({ title, subtitle, back, action, children }: Props) {
  return (
    <>
      <div className="page-heading">
        <div>
          {back && (
            <Link to={back} className="back"><Icon name="arrow" /> Back</Link>
          )}
          <h1>{title}</h1>
          {subtitle && <p>{subtitle}</p>}
        </div>
        {action}
      </div>
      {children}
    </>
  );
}
```

- [ ] **Step 6: Update `App.tsx`**

Replace the `.backdrop` and `.device` wrappers:

```tsx
  return (
    <>
      {me === undefined && <div className="loading">Loading…</div>}
      {me === null && <Login onLoggedIn={setMe} />}
      {auth && (
        <AuthContext.Provider value={auth}>
          <AppShell>
            <Routes>{/* unchanged routes */}</Routes>
          </AppShell>
        </AuthContext.Provider>
      )}
    </>
  );
```

Add `import { AppShell } from "./components/AppShell";`.

- [ ] **Step 7: Update `Login.tsx`**

Wrap the form in `<div className="login-page">`, make the form `className="card login"`, replace `<img src={logo} …>` with `<BrandMark />`, and change the `<h1>` to `Budget & insights`. Remove the `logo` import.

- [ ] **Step 8: Update `Home.tsx` and `BarChart.tsx`, and delete the old logo**

In `Home.tsx`, remove the `action={…Log out…}` prop, `onLogout`, and the now-unused `logout`/`navigate`/`useNavigate` imports. The screen is fully rewritten in Task 4, and this step only keeps the build green. In `BarChart.tsx`, change `className={b.highlight ? "bar bar-hi" : "bar"}` to `className={b.highlight ? "bar-rect bar-hi" : "bar-rect"}`. Then run `git rm frontend/src/assets/logo.svg`.

- [ ] **Step 9: Build**

Run: `cd frontend && npm run build`
Expected: `tsc --noEmit` and `vite build` succeed with no errors. `grep -rn "logo.svg\|backdrop\|device" frontend/src` returns nothing.

- [ ] **Step 10: Check it in the browser at three widths**

Run `make seed && make dev`, open `http://localhost:5173`, and log in as `desmet` (the password is printed by `make seed`). At 1280px, 800px and 390px wide (DevTools device toolbar), check:
- At 1280: full sidebar with labels, "Budget & insights" highlighted, and the name with Log out in the topbar.
- At 800: icon-only sidebar.
- At 390: no sidebar, a bottom tab bar with Budget/Goals, and Log out visible.
- Clicking Goals → New goal → Back works, and the sidebar highlight follows the route.
- In the DevTools console, `document.documentElement.scrollWidth <= innerWidth` returns `true` at each width.

- [ ] **Step 11: Commit**

```bash
git add -A frontend/src
git commit -m "feat(frontend): responsive app shell and design tokens from the budget mockup"
```

---

### Task 4: Budget & insights dashboard (Home)

**Files:**
- Modify: `frontend/src/types.ts` (append types)
- Rewrite: `frontend/src/routes/Home.tsx`
- Create: `frontend/src/routes/budget.css`

**Interfaces:**
- Consumes: Task 2's `/api/budget` JSON. From Task 3: `Icon`, `IconName`, `Piggy`, `Screen` (with `subtitle`) and the shared classes. The existing `/api/overview` (`Overview` type) supplies the accounts and the saving insight card. Also `BarChart` (`src/components/BarChart.tsx`), and `eur`, `eurWhole`, `monthLong`, `monthShort`, `longDate` (`src/format.ts`).
- Produces: nothing that later tasks rely on.

- [ ] **Step 1: Add types to `types.ts`**

```ts
export type BudgetStatus = "high" | "above" | "ok";
export type BudgetCategory = {
  category: string;
  label: string;
  amount_cents: number;
  typical_cents: number;
  usual_low_cents: number;
  usual_high_cents: number;
  status: BudgetStatus;
  note: string;
  history: MonthAmount[];
  insight_key: string | null;
  noted: boolean;
};
export type Budget = {
  month: string;
  total_cents: number;
  typical_total_cents: number;
  status: BudgetStatus;
  note: string;
  categories: BudgetCategory[];
  coverage_note: string;
};
```

- [ ] **Step 2: Write `Home.tsx`**

The layout follows the mockup's sections in order: heading, summary row, category cards, advice banner, details list, footer.
- **Heading:** the title "Budget & insights", the subtitle "See where your money went this month compared with a usual month, and what it could mean.", and a month pill on the right (no arrows).
- **Summary row:** on the left, the month total vs usual with a bar and a status pill. On the right, the accounts panel. The accounts panel replaces the mockup's "Bekijk je maandverloop" tile, so the balances shown by the old Home aren't lost.
- **Category cards:** the first 6 categories. Each card links to its detail row (`#cat-<category>`).
- **Advice banner (piggy):** when `/api/overview` returns a saving insight, it shows that headline and links to `/insights/<key>`. Otherwise it shows "Saving for something? Set a goal and see when you could reach it." and links to `/goals/new`.
- **Details:** one `<details>` row for every category, with the first one open. The expanded content has three parts: (1) a `BarChart` of `history` with the usual-range band and the last bar highlighted; (2) an insight box containing the note plus a primary link "Look at this change" → `/insights/<key>` when `insight_key` is set, with "Noted: you expect this to continue" when `noted`; (3) a "Usual month" comparison showing `typical` and the range `low–high`.
- **Footer:** `coverage_note` and "Data up to <longDate(as_of)>".

```tsx
import { Link } from "react-router-dom";
import { BarChart } from "../components/BarChart";
import { Icon, type IconName, Piggy } from "../components/Icons";
import { Screen } from "../components/Screen";
import { eur, eurWhole, longDate, monthLong, monthShort } from "../format";
import type { Budget, BudgetCategory, BudgetStatus, Overview } from "../types";
import { useLoad } from "../useLoad";
import "./budget.css";

const COLOUR: Record<BudgetStatus, "red" | "orange" | "green"> = { high: "red", above: "orange", ok: "green" };
const STATUS_TITLE: Record<BudgetStatus, string> = { high: "Unusual month", above: "Above your usual month", ok: "On track" };
const ICONS: Record<string, IconName> = {
  food: "cart", restaurants: "fork", transport: "car", clothing: "bag",
  housing_energy: "house", household_maintenance: "house", healthcare: "heart",
  subscriptions: "doc", communication: "doc", insurance_financial_services: "doc",
  leisure_culture: "trend", debt_repayment: "wallet",
};
const ACCOUNT_TYPES = { current: "Current account", savings: "Savings account", credit_card: "Credit card" } as const;

/** Share of the usual month, for the bar. Clamped so refunds and big spikes still draw sanely. */
export function barWidth(amount: number, typical: number): number {
  if (typical <= 0) return amount > 0 ? 100 : 0;
  return Math.min(100, Math.max(0, (amount / typical) * 100));
}

function percentLabel(amount: number, typical: number): string {
  return typical > 0 ? `${Math.round((amount / typical) * 100)}%` : "new";
}

function Progress({ amount, typical, label }: { amount: number; typical: number; label: string }) {
  const pct = percentLabel(amount, typical);
  return (
    <div className="progress-row">
      <div className="bar" role="img" aria-label={`${pct} of ${label}`}>
        <span style={{ width: `${barWidth(amount, typical)}%` }} />
      </div>
      <b className="percent">{pct}</b>
    </div>
  );
}

function CategoryCard({ c }: { c: BudgetCategory }) {
  return (
    <a href={`#cat-${c.category}`} className={`category ${COLOUR[c.status]}`}>
      <span className="tile-icon"><Icon name={ICONS[c.category] ?? "budget"} /></span>
      <h3>{c.label}</h3>
      <strong className="amount-big">{eurWhole(c.amount_cents)}</strong>
      <span className="of">usual {eurWhole(c.typical_cents)}</span>
      <Progress amount={c.amount_cents} typical={c.typical_cents} label="your usual month" />
      <div className="note">
        <span className="note-symbol" aria-hidden="true">{c.status === "ok" ? "✓" : "!"}</span>
        <p>{c.noted ? "Noted: you expect this to continue." : c.note}</p>
      </div>
    </a>
  );
}

function DetailRow({ c, open }: { c: BudgetCategory; open: boolean }) {
  return (
    <details className={`detail ${COLOUR[c.status]}`} id={`cat-${c.category}`} open={open}>
      <summary>
        <span className="detail-name">
          <span className="tile-icon"><Icon name={ICONS[c.category] ?? "budget"} /></span>
          <b>{c.label}</b>
          <span className="fold" aria-hidden="true">⌄</span>
        </span>
        <span className="detail-amount"><b>{eur(c.amount_cents)}</b> <span>usual {eur(c.typical_cents)}</span></span>
        <Progress amount={c.amount_cents} typical={c.typical_cents} label="your usual month" />
      </summary>
      <div className="detail-content">
        <section>
          <h4>Last {c.history.length} months</h4>
          <BarChart
            bars={c.history.map((h, i) => ({ label: monthShort(h.month), value: h.amount_cents, highlight: i === c.history.length - 1 }))}
            band={{ low: c.usual_low_cents, high: c.usual_high_cents }}
          />
          <p className="small muted">Shaded: your usual range</p>
        </section>
        <section className="tip">
          <h4>{STATUS_TITLE[c.status]}</h4>
          <p>{c.note}</p>
          {c.noted && <span className="chip">Noted: you expect this to continue</span>}
          {c.insight_key && (
            <Link className="btn btn-primary" to={`/insights/${encodeURIComponent(c.insight_key)}`}>
              Look at this change <Icon name="chevron" />
            </Link>
          )}
        </section>
        <section className="comparison">
          <h4>Your usual month</h4>
          <strong>{eurWhole(c.typical_cents)}</strong>
          <p>Usually between {eurWhole(c.usual_low_cents)} and {eurWhole(c.usual_high_cents)}.</p>
        </section>
      </div>
    </details>
  );
}

export function Home() {
  const budget = useLoad<Budget>("/budget");
  const overview = useLoad<Overview>("/overview");
  const error = budget.error ?? overview.error;
  const b = budget.data;
  const o = overview.data;
  const saving = o?.insights.find((i) => i.type === "saving");

  return (
    <Screen
      title="Budget & insights"
      subtitle="See where your money went this month compared with a usual month, and what it could mean."
      action={b && <span className="month-pill">{monthLong(b.month)}</span>}
    >
      {error && <p className="error">{error}</p>}
      {!error && (!b || !o) && <p className="muted">Loading…</p>}
      {b && o && (
        <>
          <div className="summary-row">
            <section className={`card month-summary ${COLOUR[b.status]}`} aria-label="This month">
              <div className="month-number">
                <h3>{monthLong(b.month)}</h3>
                <strong>{eur(b.total_cents)}</strong>
                <p>usual {eur(b.typical_total_cents)}</p>
              </div>
              <Progress amount={b.total_cents} typical={b.typical_total_cents} label="a usual month" />
              <div className="status-pill">
                <span className="dot" aria-hidden="true" />
                <div><strong>{STATUS_TITLE[b.status]}</strong><p>{b.note}</p></div>
              </div>
            </section>
            <section className="card accounts" aria-label="Accounts">
              {o.accounts.map((a) => (
                <div key={a.id} className="account">
                  <span className="small muted">{ACCOUNT_TYPES[a.type]}</span>
                  <b className={a.balance_cents < 0 ? "neg" : undefined}>{eur(a.balance_cents)}</b>
                </div>
              ))}
            </section>
          </div>

          {b.categories.length === 0 ? (
            <div className="card muted">{b.note}</div>
          ) : (
            <section aria-labelledby="categories-title">
              <div className="section-heading">
                <h2 id="categories-title">Spending by category</h2>
                <span className="unit-label">€ this month · % of your usual month</span>
              </div>
              <div className="categories">
                {b.categories.slice(0, 6).map((c) => <CategoryCard key={c.category} c={c} />)}
              </div>
            </section>
          )}

          <div className="advice-banner">
            <Piggy />
            <div className="banner-copy">
              <h2>{saving ? "You're saving more" : "Saving for something?"}</h2>
              <p>{saving ? saving.headline : "Set a goal and see when you could reach it."}</p>
            </div>
            <Link className="btn btn-primary banner-cta" to={saving ? `/insights/${encodeURIComponent(saving.key)}` : "/goals/new"}>
              {saving ? "Connect it to a goal" : "Set a goal"} <Icon name="arrow" />
            </Link>
          </div>

          {b.categories.length > 0 && (
            <section aria-labelledby="details-title">
              <div className="section-heading"><h2 id="details-title">Details per category</h2></div>
              {b.categories.map((c, i) => <DetailRow key={c.category} c={c} open={i === 0} />)}
            </section>
          )}

          <footer className="page-footer">
            <span>{b.coverage_note}</span>
            <span>Data up to {longDate(o.as_of)}</span>
          </footer>
        </>
      )}
    </Screen>
  );
}
```

Every `ICONS` key must be a real `SPENDING_LABELS` key (`backend/app/engine/types.py`). Unknown categories fall back to `"budget"`.

- [ ] **Step 3: Write `budget.css`**

Port these mockup rules with their exact values, keeping the class names used above. Only these deliberate renames apply:
- `.month` becomes `.month-pill`, a single pill with no arrow spans: `border: 1px solid var(--line); border-radius: 9px; background: #fff; padding: 9px 18px; font-weight: 600; font-size: 12px; white-space: nowrap`.
- The mockup's `.category .amount` becomes `.amount-big`, to avoid clashing with the shared `.amount`.
- `.ontrack` becomes `.status-pill`, coloured by the scope rather than always green: `background: var(--colorwash)`, the `strong` uses `color: var(--strong)`, and `.dot` uses `background: var(--color)`, 10px round.
- The mockup's `.progress` becomes `.progress-row` (`display: flex; align-items: center; gap: 7px; margin: 13px 0 9px`), because `.progress` is the goal bar.
- `.category-heading` and `.details-heading` become `.section-heading`.
- `.month-link` becomes `.accounts`, a column of `.account` rows (`display: flex; justify-content: space-between; gap: 12px; padding: 6px 0; border-top: 1px solid var(--line)`, with no border on the first row).

Port these unchanged: `.summary-row` (with `grid-template-columns: 1fr 260px`), `.month-summary` (with the `.bar` height 19px inside it), `.month-number`, `.categories` (`repeat(6, minmax(0, 1fr))`), `.category` and its `h3`, `.of`, `.note`, `.note-symbol`, `.red .note`, `.orange .note`, `.red .tile-icon`, `.unit-label`, `.advice-banner`, `.pig`, `.banner-copy`, `.detail`, `.detail > summary` (5-column grid → use 3 columns: `minmax(210px, 1.55fr) minmax(160px, 1fr) minmax(160px, 1.1fr)`), `.detail-name`, `.fold`, `.detail[open] .fold`, `.detail-amount`, `.detail-content` (`1.4fr 1fr 1fr`), `.tip` (with `.tip h4 { color: var(--strong) }`), `.comparison` (use the neutral `#eef5fc` background, `color: var(--ink)`), and the `footer` rule becoming `.page-footer`.

Add the following:
- `.banner-cta { width: auto; margin-left: auto; white-space: nowrap; }`. Put this one in **`styles.css`**, not `budget.css`, because Task 5's Goals page reuses it.
- `.category { min-width: 0; overflow-wrap: anywhere; color: inherit; }`
- `.detail .bar-hi { fill: var(--color); }`
- `.detail > summary .progress-row { margin: 0; }`
- `.tip .btn { width: auto; margin-top: 10px; align-self: flex-start; }`
- `.tip { display: flex; flex-direction: column; gap: 6px; }`

Add these breakpoints, adapted from the mockup's 1150/950/650 blocks:

```css
@media (max-width: 1150px) {
  .summary-row { grid-template-columns: 1fr 220px; }
  .categories { grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; }
  .detail-content { grid-template-columns: 1fr 1fr; }
  .detail-content > section:first-child { grid-column: 1 / -1; }
}
@media (max-width: 950px) {
  .summary-row { grid-template-columns: 1fr; }
  .month-summary { flex-wrap: wrap; }
  .detail > summary { grid-template-columns: 1.3fr 1fr; }
  .detail > summary .progress-row { grid-column: 1 / -1; }
}
@media (max-width: 650px) {
  .categories { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .category { padding: 14px 12px; }
  .amount-big { font-size: 20px; }
  .status-pill { width: 100%; }
  .advice-banner { flex-wrap: wrap; padding: 14px; gap: 10px; }
  .pig { width: 82px; height: 62px; align-self: center; }
  .banner-cta { width: 100%; }
  .detail > summary { grid-template-columns: 1fr auto; gap: 8px; padding: 12px; }
  .detail-content { grid-template-columns: 1fr; padding: 12px; }
  .page-footer { flex-direction: column; gap: 6px; }
}
```

The mockup's `@media (min-width: 1450px)` block ports as-is, with the class renames above.

- [ ] **Step 4: Build**

Run: `cd frontend && npm run build`
Expected: success.

- [ ] **Step 5: Check it in the browser as De Smet** (`make seed && make dev`)

Expected at 1280px:
- The summary reads "September 2026 · €7,180.87 · usual €5,533.72", with an orange "Above your usual month" pill and "You spent €1,647 more than in a usual month."
- There are 6 cards in one row, in this order: Groceries (red), Healthcare (red), Children & school (orange), Clothing (orange), Leisure & culture (orange), Housing & energy (green).
- The Groceries detail is open, with a 6-bar chart whose last bar is red, and "Look at this change" goes to the grocery insight.
- The banner reads "Saving for something?" and goes to `/goals/new`.

Then log in as `jean`: all cards are green, and the banner reads "You're saving more" and opens the saving insight.

- [ ] **Step 6: Check the edge cases**

- At 390px, the cards are 2-up, "Insurance & bank fees" (Jean's third category) wraps inside its card, and `document.documentElement.scrollWidth <= innerWidth` is `true`.
- As `desmet`: open Groceries → click "Look at this change" → "Dismiss" → you land back on `/`, and Groceries is now **orange** with no "Look at this change" button.
- Run `make seed` again to reset, then choose "Expected to continue" on Groceries → return to `/`. The Groceries card now says "Noted: you expect this to continue."

- [ ] **Step 7: Commit**

```bash
git add frontend/src/types.ts frontend/src/routes/Home.tsx frontend/src/routes/budget.css
git commit -m "feat(frontend): budget & insights dashboard as the home screen"
```

---

### Task 5: Restyle Insight, Scenario, Goals and GoalForm for wide screens

Logic stays untouched. Only wrappers and classes change, so that desktop uses the space and phones stay single-column.

**Files:**
- Modify: `frontend/src/routes/Insight.tsx`, `Scenario.tsx`, `Goals.tsx`, `GoalForm.tsx`
- Modify: `frontend/src/styles.css` (append a "two-column pages" section)

**Interfaces:**
- Consumes: `Screen` (Task 3) and the shared classes.
- Produces: the CSS classes `.split`, `.split-main`, `.split-side` and `.goal-grid`.

- [ ] **Step 1: Add the layout classes to `styles.css`**

```css
/* Two-column pages: main column + side column on wide screens, stacked on narrow ones. */
.split { display: grid; grid-template-columns: minmax(0, 1.6fr) minmax(0, 1fr); gap: 18px; align-items: start; }
.split-main, .split-side { display: flex; flex-direction: column; gap: 14px; min-width: 0; }
.goal-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
.actions { display: flex; gap: 10px; flex-wrap: wrap; }
.actions .btn { width: auto; }
@media (max-width: 950px) { .split { grid-template-columns: 1fr; } }
@media (max-width: 650px) { .actions .btn { width: 100%; } }
```

- [ ] **Step 2: `Insight.tsx`**

Inside the `data && (…)` fragment, wrap the content in `<div className="split">`:
- `.split-main` gets the headline and chart card, the spending question card (or the saving question card), and the "See the impact" link.
- `.split-side` gets the "Why you're seeing this" `<details>`, the transactions card and the coverage note.

Change the "See the impact" `Link`'s className to `btn btn-primary` and wrap it in `<div className="actions">`. Also pass `subtitle={data?.question}` to `Screen`. Change nothing else.

- [ ] **Step 3: `Scenario.tsx`**

Wrap the `data && (…)` content in `<div className="split">`:
- `.split-main` gets the two scenario cards (the existing `grid-2`), the warning and the balances table card.
- `.split-side` gets the "What's included" card and the assumptions `<details>`.

Pass `subtitle="Compare what happens if this was a one-off with what happens if it continues."` to `Screen`. Keep the segmented control above the split.

- [ ] **Step 4: `Goals.tsx`**

Wrap the `data.goals.map(…)` output in `<div className="goal-grid">`. Move the "New goal" link into `Screen`'s `action` prop as `<Link to="/goals/new" className="btn btn-primary banner-cta">New goal</Link>`, rendered only when `data` has loaded. `.banner-cta` already lives in `styles.css` (Task 4). Change `back="/"` to no `back` at all: Goals is now a top-level nav destination.

- [ ] **Step 5: `GoalForm.tsx`**

Wrap the returned content (after the kind `segmented`) in `<div className="split">`:
- `.split-main` gets the form card and the save/delete buttons, wrapped in `<div className="actions">`.
- `.split-side` gets the estimate card, the next-steps card and the message.

Keep the loading, error and not-found early returns unchanged.

- [ ] **Step 6: Build and check in the browser**

Run: `cd frontend && npm run build` (expect success). Then with `make dev`, as `desmet`:
- Insight → See the impact → 1/2/3 months all render, and at 1280 there are two columns while at 390 they stack.
- As `jean`: Insight → Car → fill in €15,000 → an estimate appears on the right at 1280 and below at 390 → Create goal → the Goals grid shows the card.
- Run `document.documentElement.scrollWidth <= innerWidth` on each page at 390.

- [ ] **Step 7: Commit**

```bash
git add frontend/src
git commit -m "feat(frontend): two-column insight, scenario and goal pages on wide screens"
```

---

### Task 6: Final verification and docs

**Files:**
- Modify: `PROJECT-INFO.md`, `README.md`

- [ ] **Step 1: Full test suite and production build**

Run: `make test && make build`
Expected: all pytest tests pass (the existing ones plus the 2 new files), and the frontend builds.

- [ ] **Step 2: Walk the production bundle through**

Run `make seed && make serve`, open `http://localhost:8000`, and repeat the De Smet and Jean walkthroughs from Task 4 step 5 and Task 5 step 6 at 1920, 1280, 800 and 390px. Refreshing on `/goals` and on `/insights/spend:food:2026-09` must load the page (the SPA fallback), not return 404.

- [ ] **Step 3: Update `PROJECT-INFO.md`**

Under **Open questions**, add:
- **UI look?** → It matches `kbc-budget-inzichten.html`: a responsive desktop shell with a sidebar that becomes icons below 950px and a bottom tab bar below 650px. The copy is English (decided 2026-09-30). The weekly in-month chart and the month switcher were left out because "today" is a completed month.

Under **Key discoveries**, add:
- The budget dashboard's colours come from the engine. Red means the detector flagged the category and the insight is still visible. Orange means more than 10% above the usual month (`ABOVE_USUAL_PERCENT`). Green covers everything else. So De Smet's back-to-school rise is orange, not red, and dismissing an insight turns its card orange.

Under **Known gotchas**, add:
- Monthly category totals can be negative when refunds exceed spending (De Smet's leisure in Apr 2026). Bars clamp to 0–100%.
- `.bar` is the HTML progress track. SVG chart rectangles use `.bar-rect`.

- [ ] **Step 4: Update `README.md`**

Where the README describes the screens or the phone frame, replace that text with a one-paragraph description of the Budget & insights home and the responsive layout. Add `GET /api/budget` wherever the README lists endpoints. Read the README first and change only those sections.

- [ ] **Step 5: Commit**

```bash
git add PROJECT-INFO.md README.md
git commit -m "docs: budget dashboard, responsive layout and colour rules"
```
