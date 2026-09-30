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
