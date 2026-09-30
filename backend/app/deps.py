from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .config import Settings, get_settings
from .db import SessionLocal
from .models import AuthSession, Customer
from .security import hash_token, utcnow


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


DbSession = Annotated[Session, Depends(get_db)]
AppSettings = Annotated[Settings, Depends(get_settings)]


SESSION_COOKIE = "tm_session"


def get_current_customer(request: Request, db: DbSession) -> Customer:
    """The only source of customer identity: the server-side session behind the cookie."""
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        session = db.get(AuthSession, hash_token(token))
        if session is not None and session.expires_at > utcnow():
            customer = db.get(Customer, session.customer_id)
            if customer is not None:
                return customer
    raise HTTPException(status_code=401, detail="Please log in.")


CurrentCustomer = Annotated[Customer, Depends(get_current_customer)]
