from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON, Text
from datetime import datetime
from app.core.database import Base

class RefundPolicy(Base):
    __tablename__ = "refund_policies"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), unique=True, nullable=False)
    policy_type = Column(String, default="FLEXIBLE")  # FLEXIBLE, MODERATE, STRICT, NON_REFUNDABLE, CUSTOM
    rules = Column(JSON, default=list)  # [{"hours_before": 168, "refund_pct": 100}, {"hours_before": 72, "refund_pct": 75}]
    description = Column(Text, nullable=True)


class RefundRequest(Base):
    __tablename__ = "refund_requests"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    booking_id = Column(Integer, nullable=True)
    quantity_refunded = Column(Integer, default=1, nullable=False)
    inventory_restored = Column(Integer, default=0, nullable=False)  # 0=False, 1=True for SQLite/Postgres compatibility
    amount_requested = Column(Float, nullable=False)

    amount_approved = Column(Float, default=0.0)
    reason = Column(Text, nullable=True)
    status = Column(String, default="REQUESTED")  # REQUESTED, APPROVED, PROCESSING, REFUNDED, REJECTED
    reviewed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
