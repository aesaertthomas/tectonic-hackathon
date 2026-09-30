from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True)
    display_name: Mapped[str] = mapped_column(String(100))
    password_hash: Mapped[str] = mapped_column(String(255))
    cash_buffer_cents: Mapped[int] = mapped_column(Integer)
    data_as_of: Mapped[date] = mapped_column(Date)


class AuthSession(Base):
    __tablename__ = "sessions"
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime)


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    external_ref: Mapped[str] = mapped_column(String(40))
    name: Mapped[str] = mapped_column(String(100))
    number: Mapped[str] = mapped_column(String(40))
    type: Mapped[str] = mapped_column(String(20))  # current | savings | credit_card
    balance_cents: Mapped[int] = mapped_column(Integer)


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"))
    external_ref: Mapped[str] = mapped_column(String(40))
    booked_on: Mapped[date] = mapped_column(Date, index=True)
    amount_cents: Mapped[int] = mapped_column(Integer)
    counterparty: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(40))
    kind: Mapped[str] = mapped_column(String(20))  # income | expense | refund | internal_transfer
    recurring: Mapped[bool] = mapped_column(Boolean)
    category_override: Mapped[str | None] = mapped_column(String(40), nullable=True)


class RecurringItemRow(Base):
    __tablename__ = "recurring_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    label: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(40))
    amount_cents: Mapped[int] = mapped_column(Integer)  # + into the current account, - out of it
    frequency: Mapped[str] = mapped_column(String(20))  # monthly | monthly_except | yearly
    months: Mapped[str] = mapped_column(String(40))  # active months "1,2,9"; "" for monthly
    confirmed: Mapped[bool] = mapped_column(Boolean)


class InsightFeedback(Base):
    __tablename__ = "insight_feedback"
    __table_args__ = (UniqueConstraint("customer_id", "insight_key"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    insight_key: Mapped[str] = mapped_column(String(64))
    response: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime)


class Goal(Base):
    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id", ondelete="CASCADE"), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(60))
    target_cents: Mapped[int] = mapped_column(Integer)
    target_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    earmarked_cents: Mapped[int] = mapped_column(Integer)
    monthly_contribution_cents: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime)
