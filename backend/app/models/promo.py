from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON, Boolean
from datetime import datetime
from app.core.database import Base

class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    discount_type = Column(String, default="PERCENTAGE")  # PERCENTAGE, FIXED
    discount_value = Column(Float, nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    expiry_date = Column(DateTime, nullable=True)
    max_uses = Column(Integer, default=100)
    used_count = Column(Integer, default=0)
    per_user_limit = Column(Integer, default=1)
    min_order_amount = Column(Float, default=0.0)
    max_discount_amount = Column(Float, nullable=True)
    applicable_event_ids = Column(JSON, default=list)  # Empty list = all events
    applicable_ticket_tiers = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PromoRedemption(Base):
    __tablename__ = "promo_redemptions"

    id = Column(Integer, primary_key=True, index=True)
    promo_id = Column(Integer, ForeignKey("promo_codes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    booking_draft_id = Column(Integer, nullable=True)
    discount_amount = Column(Float, nullable=False)
    redeemed_at = Column(DateTime, default=datetime.utcnow)
