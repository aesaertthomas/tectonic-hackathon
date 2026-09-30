"""Customer-scoped data access. Every function takes customer_id and filters on it: this is the IDOR boundary."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .engine.baseline import analysis_month, first_full_month
from .engine.types import Kind, RecurringItem, Txn
from .models import Account, Customer, Goal, InsightFeedback, RecurringItemRow, Transaction
from .security import utcnow


def accounts(db: Session, customer_id: int) -> list[Account]:
    return list(db.scalars(select(Account).where(Account.customer_id == customer_id).order_by(Account.id)))


def savings_balance(db: Session, customer_id: int) -> int:
    total = db.scalar(
        select(func.coalesce(func.sum(Account.balance_cents), 0)).where(
            Account.customer_id == customer_id, Account.type == "savings"
        )
    )
    return int(total or 0)


def transactions(db: Session, customer_id: int) -> list[Txn]:
    rows = db.scalars(
        select(Transaction).where(Transaction.customer_id == customer_id).order_by(Transaction.booked_on, Transaction.id)
    )
    return [
        Txn(
            id=row.id,
            account_id=row.account_id,
            booked_on=row.booked_on,
            amount_cents=row.amount_cents,
            counterparty=row.counterparty,
            category=row.category_override or row.category,
            kind=Kind(row.kind),
            recurring=row.recurring,
        )
        for row in rows
    ]


def schedule(db: Session, customer_id: int) -> list[RecurringItem]:
    rows = db.scalars(select(RecurringItemRow).where(RecurringItemRow.customer_id == customer_id).order_by(RecurringItemRow.id))
    return [
        RecurringItem(
            label=row.label,
            category=row.category,
            amount_cents=row.amount_cents,
            frequency=row.frequency,
            months=tuple(int(m) for m in row.months.split(",") if m),
            confirmed=row.confirmed,
        )
        for row in rows
    ]


def set_category_override(db: Session, customer_id: int, txn_ids: Iterable[int], category: str) -> None:
    ids = list(txn_ids)
    if not ids:
        return
    db.execute(
        update(Transaction)
        .where(Transaction.customer_id == customer_id, Transaction.id.in_(ids))
        .values(category_override=category)
    )


def feedback_map(db: Session, customer_id: int) -> dict[str, str]:
    rows = db.scalars(select(InsightFeedback).where(InsightFeedback.customer_id == customer_id))
    return {row.insight_key: row.response for row in rows}


def upsert_feedback(db: Session, customer_id: int, key: str, response: str) -> None:
    def find() -> InsightFeedback | None:
        return db.scalar(
            select(InsightFeedback).where(InsightFeedback.customer_id == customer_id, InsightFeedback.insight_key == key)
        )

    existing = find()
    if existing is None:
        try:
            with db.begin_nested():  # savepoint: a lost race must not undo the caller's other pending changes
                db.add(InsightFeedback(customer_id=customer_id, insight_key=key, response=response, created_at=utcnow()))
        except IntegrityError:  # a concurrent request inserted the same row first
            existing = find()
    if existing is not None:
        existing.response = response
        existing.created_at = utcnow()


def goals(db: Session, customer_id: int) -> list[Goal]:
    return list(db.scalars(select(Goal).where(Goal.customer_id == customer_id).order_by(Goal.id)))


def goal(db: Session, customer_id: int, goal_id: int) -> Goal | None:
    return db.scalar(select(Goal).where(Goal.id == goal_id, Goal.customer_id == customer_id))


def total_earmarked(db: Session, customer_id: int, exclude_goal_id: int | None = None) -> int:
    query = select(func.coalesce(func.sum(Goal.earmarked_cents), 0)).where(Goal.customer_id == customer_id)
    if exclude_goal_id is not None:
        query = query.where(Goal.id != exclude_goal_id)
    return int(db.scalar(query) or 0)


@dataclass(frozen=True)
class CustomerData:
    """Everything the engine needs for one customer."""

    txns: list[Txn]
    schedule: list[RecurringItem]
    savings_ids: frozenset[int]
    current_balance: int
    savings_balance: int
    cash_buffer: int
    as_of: date
    analysis_month: date
    first_full_month: date


def load_customer_data(db: Session, customer: Customer) -> CustomerData | None:
    txns = transactions(db, customer.id)
    if not txns:
        return None
    accs = accounts(db, customer.id)
    return CustomerData(
        txns=txns,
        schedule=schedule(db, customer.id),
        savings_ids=frozenset(a.id for a in accs if a.type == "savings"),
        current_balance=sum(a.balance_cents for a in accs if a.type == "current"),
        savings_balance=sum(a.balance_cents for a in accs if a.type == "savings"),
        cash_buffer=customer.cash_buffer_cents,
        as_of=customer.data_as_of,
        analysis_month=analysis_month(customer.data_as_of),
        first_full_month=first_full_month(txns[0].booked_on),
    )
