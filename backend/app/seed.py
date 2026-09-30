"""Import the synthetic dataset (sim-user-data.json) into SQLite.

Run from backend/:  .venv/bin/python -m app.seed [path/to/sim-user-data.json]
The dataset is fictional. Demo passwords are generated here (or read from DEMO_PASSWORD) and printed once.
"""

import json
import secrets
import sys
from calendar import monthrange
from datetime import date
from decimal import Decimal
from functools import lru_cache
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from .config import REPO_ROOT, get_settings
from .db import Base, engine
from .engine.types import SPENDING_CATEGORIES, Kind
from .models import Account, Customer, RecurringItemRow, Transaction
from .security import hash_password

DEFAULT_DATASET = REPO_ROOT / "sim-user-data.json"
ACCOUNT_TYPES = frozenset({"current", "savings", "credit_card"})
FREQUENCIES = frozenset({"monthly", "monthly_except", "yearly"})

# Demo settings per profile: username, greeting name, cash buffer in cents.
DEMO_PROFILES: dict[str, tuple[str, str, int]] = {
    "BE001": ("jean", "Jean", 100_000),
    "BE002": ("desmet", "Sophie & Thomas", 100_000),
    "BE003": ("lucas", "Lucas", 20_000),
}
DEFAULT_BUFFER_CENTS = 50_000


def to_cents(value: Any) -> int:
    return int((Decimal(str(value)) * 100).quantize(Decimal("1")))


@lru_cache
def load_dataset(path: str) -> dict[str, Any]:
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _period_end(period_to: str) -> date:
    year, month = (int(part) for part in period_to.split("-"))
    return date(year, month, monthrange(year, month)[1])


def _masked_number(account_type: str, profile_index: int, account_index: int) -> str:
    """Fictitious masked account numbers for display."""
    suffix = f"{profile_index}{account_index:03d}"
    if account_type == "credit_card":
        return f"•••• •••• •••• {suffix}"
    return f"BE•• •••• •••• {suffix}"


def import_dataset(db: Session, dataset: dict[str, Any], password: str | None = None) -> dict[str, str]:
    """Insert every profile. Returns {username: password}. Raises ValueError on unexpected data."""
    as_of = _period_end(dataset["dataset"]["period"]["to"])
    credentials: dict[str, str] = {}
    for index, profile in enumerate(dataset["profiles"], start=1):
        username, greeting, buffer = DEMO_PROFILES.get(
            profile["id"], (profile["id"].lower(), profile["name"].split()[0], DEFAULT_BUFFER_CENTS)
        )
        pw = password or secrets.token_urlsafe(12)
        _import_profile(db, profile, index, username, greeting, buffer, as_of, pw)
        credentials[username] = pw
    db.commit()
    return credentials


def _import_profile(
    db: Session, profile: dict[str, Any], index: int, username: str, greeting: str, buffer: int, as_of: date, password: str
) -> None:
    customer = Customer(
        username=username,
        display_name=greeting,
        password_hash=hash_password(password),
        cash_buffer_cents=buffer,
        data_as_of=as_of,
    )
    db.add(customer)
    db.flush()

    closing = profile["monthly_summary"][-1]["closing_balances_eur"]
    accounts: dict[str, Account] = {}
    for n, acc in enumerate(profile["accounts"], start=1):
        if acc["type"] not in ACCOUNT_TYPES:
            raise ValueError(f"Unknown account type {acc['type']!r} in {acc['id']}")
        row = Account(
            customer_id=customer.id,
            external_ref=acc["id"],
            name=acc["name"],
            number=_masked_number(acc["type"], index, n),
            type=acc["type"],
            balance_cents=to_cents(closing[acc["id"]]),
        )
        db.add(row)
        accounts[acc["id"]] = row
    db.flush()

    for t in profile["transactions"]:
        kind = Kind(t["type"])
        if kind in (Kind.EXPENSE, Kind.REFUND) and t["category"] not in SPENDING_CATEGORIES:
            raise ValueError(f"Unknown spending category {t['category']!r} in {t['id']}")
        db.add(
            Transaction(
                customer_id=customer.id,
                account_id=accounts[t["account_id"]].id,
                external_ref=t["id"],
                booked_on=date.fromisoformat(t["date"]),
                amount_cents=to_cents(t["amount"]),
                counterparty=t["merchant"],
                category=t["category"],
                kind=kind.value,
                recurring=bool(t.get("recurring", False)),
            )
        )

    for r in profile["recurring"]:
        if r["frequency"] not in FREQUENCIES:
            raise ValueError(f"Unknown frequency {r['frequency']!r} for {r['merchant']}")
        into_current = r["kind"] == "income" or r["category"] == "transfer_from_savings"
        amount = to_cents(r["amount_eur"])
        db.add(
            RecurringItemRow(
                customer_id=customer.id,
                label=r["merchant"],
                category=r["category"],
                amount_cents=amount if into_current else -amount,
                frequency=r["frequency"],
                months=",".join(str(m) for m in r.get("months", [])),
                confirmed=not r.get("variable_amount", False),
            )
        )


def main(argv: list[str]) -> None:
    path = Path(argv[1]) if len(argv) > 1 else DEFAULT_DATASET
    dataset = load_dataset(str(path))
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        credentials = import_dataset(db, dataset, get_settings().demo_password or None)
    print("Demo customers. Passwords are shown once and stored only as hashes:")
    for username, pw in credentials.items():
        print(f"  {username:<8} {pw}")


if __name__ == "__main__":
    main(sys.argv)
