from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.core.database import Base

class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    preference_key = Column(String, nullable=False, index=True)  # e.g. preferred_location, preferred_tier, preferred_category
    preference_value = Column(String, nullable=False)
    confidence = Column(Float, default=0.9)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BookingDraft(Base):
    __tablename__ = "booking_drafts"

    id = Column(Integer, primary_key=True, index=True)
    draft_number = Column(String, unique=True, index=True, nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, default=1)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    ticket_type = Column(String, default="Standard")
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, nullable=False)
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    idempotency_key = Column(String, unique=True, index=True, nullable=True)
    status = Column(String, default="DRAFT")  # DRAFT, READY_FOR_PAYMENT, PAYMENT_PENDING, CONFIRMED, CANCELLED, EXPIRED
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at and self.status in ["DRAFT", "READY_FOR_PAYMENT", "PAYMENT_PENDING"]
