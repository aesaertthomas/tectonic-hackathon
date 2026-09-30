from fastapi import HTTPException
from sqlalchemy.orm import Session

from .. import repo, services
from ..engine.insights import Insight
from ..models import Customer


def load_insight(db: Session, customer: Customer, key: str) -> tuple[repo.CustomerData, Insight]:
    """Insight keys are only valid if the engine currently computes them for *this* customer."""
    data = repo.load_customer_data(db, customer)
    insight = services.find_insight(data, key)
    if data is None or insight is None:
        raise HTTPException(status_code=404, detail="Insight not found.")
    return data, insight
