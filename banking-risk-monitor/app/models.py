from datetime import datetime
from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_ref: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    average_amount: Mapped[float] = mapped_column(Float, default=100.0)
    normal_start_hour: Mapped[int] = mapped_column(Integer, default=8)
    normal_end_hour: Mapped[int] = mapped_column(Integer, default=20)
    known_devices: Mapped[str] = mapped_column(Text, default="")
    known_locations: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="customer")

class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)
    amount: Mapped[float] = mapped_column(Float)
    merchant_category: Mapped[str] = mapped_column(String(80))
    location: Mapped[str] = mapped_column(String(120))
    device_id: Mapped[str] = mapped_column(String(80))
    transaction_type: Mapped[str] = mapped_column(String(50))
    account_age_days: Mapped[int] = mapped_column(Integer)
    customer_average: Mapped[float] = mapped_column(Float)
    rule_score: Mapped[int] = mapped_column(Integer, default=0)
    ml_score: Mapped[float] = mapped_column(Float, default=0)
    final_score: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[str] = mapped_column(String(16), default="LOW")
    reasons: Mapped[str] = mapped_column(Text, default="[]")
    customer: Mapped[Customer] = relationship(back_populates="transactions")
    alert: Mapped["RiskAlert | None"] = relationship(back_populates="transaction", uselist=False)

class RiskAlert(Base):
    __tablename__ = "risk_alerts"
    id: Mapped[int] = mapped_column(primary_key=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), unique=True)
    level: Mapped[str] = mapped_column(String(16), index=True)
    status: Mapped[str] = mapped_column(String(32), default="OPEN", index=True)
    rag_explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    transaction: Mapped[Transaction] = relationship(back_populates="alert")
    reviews: Mapped[list["RiskReview"]] = relationship(back_populates="alert")

class RiskReview(Base):
    __tablename__ = "risk_reviews"
    id: Mapped[int] = mapped_column(primary_key=True)
    alert_id: Mapped[int] = mapped_column(ForeignKey("risk_alerts.id"))
    action: Mapped[str] = mapped_column(String(32))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    alert: Mapped[RiskAlert] = relationship(back_populates="reviews")
