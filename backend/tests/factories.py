"""Builders for engine unit tests."""

from datetime import date
from itertools import count

from app.engine.money import add_months
from app.engine.types import Kind, RecurringItem, Txn

FEB = date(2026, 2, 1)
MAR = date(2026, 3, 1)
JUN = date(2026, 6, 1)
AUG = date(2026, 8, 1)
SEP = date(2026, 9, 1)
OCT = date(2026, 10, 1)

_ids = count(1)


def txn(
    booked_on: date,
    amount_cents: int,
    category: str,
    kind: Kind = Kind.EXPENSE,
    account_id: int = 1,
    recurring: bool = False,
    counterparty: str = "TEST",
) -> Txn:
    return Txn(
        id=next(_ids),
        account_id=account_id,
        booked_on=booked_on,
        amount_cents=amount_cents,
        counterparty=counterparty,
        category=category,
        kind=kind,
        recurring=recurring,
    )


def monthly(
    first_month: date,
    amounts_eur: list[int],
    category: str,
    kind: Kind = Kind.EXPENSE,
    account_id: int = 1,
    recurring: bool = False,
    sign: int | None = None,
    day: int = 10,
) -> list[Txn]:
    """One transaction per month starting at first_month. Expenses default to negative amounts."""
    if sign is None:
        sign = -1 if kind == Kind.EXPENSE else 1
    return [
        txn(add_months(first_month, i).replace(day=day), sign * eur * 100, category, kind, account_id, recurring)
        for i, eur in enumerate(amounts_eur)
    ]


def item(label: str, amount_eur: int, frequency: str = "monthly", months: tuple[int, ...] = (), confirmed: bool = True, category: str = "other") -> RecurringItem:
    return RecurringItem(label, category, amount_eur * 100, frequency, months, confirmed)
