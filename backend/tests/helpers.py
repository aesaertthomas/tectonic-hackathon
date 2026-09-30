from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer
from app.security import hash_password

PASSWORD = "correct-horse-battery"
AS_OF = date(2026, 9, 30)


def add_customer(
    db: Session, username: str, password: str = PASSWORD, display_name: str | None = None, cash_buffer_cents: int = 50_000
) -> Customer:
    customer = Customer(
        username=username,
        display_name=display_name or username.title(),
        password_hash=hash_password(password),
        cash_buffer_cents=cash_buffer_cents,
        data_as_of=AS_OF,
    )
    db.add(customer)
    db.commit()
    return customer


def get_customer(db: Session, username: str) -> Customer:
    customer = db.scalar(select(Customer).where(Customer.username == username))
    assert customer is not None
    return customer


def login(client, username: str, password: str = PASSWORD):
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response
