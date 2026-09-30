from fastapi import APIRouter

from .. import repo, services
from ..deps import CurrentCustomer, DbSession
from ..engine.insights import visible_insights
from ..engine.texts import COVERAGE_NOTE
from ..schemas import AccountOut, InsightCardOut, OverviewOut

router = APIRouter(prefix="/api", tags=["overview"])


@router.get("/overview", response_model=OverviewOut)
def overview(customer: CurrentCustomer, db: DbSession) -> OverviewOut:
    data = repo.load_customer_data(db, customer)
    feedback = repo.feedback_map(db, customer.id)
    cards = [
        InsightCardOut(key=i.key, type=i.type, headline=i.headline, noted=feedback.get(i.key) == "ongoing")
        for i in visible_insights(services.all_insights(data), feedback)
    ]
    return OverviewOut(
        display_name=customer.display_name,
        as_of=customer.data_as_of,
        accounts=[AccountOut.model_validate(a) for a in repo.accounts(db, customer.id)],
        insights=cards,
        coverage_note=COVERAGE_NOTE,
    )
