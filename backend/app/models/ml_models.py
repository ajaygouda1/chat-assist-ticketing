from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, JSON, Boolean
from datetime import datetime
from app.core.database import Base

class IntentTrainingExample(Base):
    __tablename__ = "intent_training_examples"

    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    intent_label = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class FraudFlag(Base):
    __tablename__ = "fraud_flags"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    booking_id = Column(Integer, nullable=True)
    score = Column(Float, nullable=False)
    reason = Column(String, nullable=False)
    status = Column(String, default="PENDING_REVIEW")  # PENDING_REVIEW, CLEARED, CONFIRMED
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

class Reservation(Base):
    __tablename__ = "reservations"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    quantity = Column(Integer, default=1)
    status = Column(String, default="HOLD")  # HOLD, EXPIRED, CONFIRMED
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class Payout(Base):
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="PROCESSING")  # PROCESSING, COMPLETED, FAILED
    scheduled_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime, nullable=True)

class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True, index=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referred_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reward_status = Column(String, default="PENDING")  # PENDING, REWARDED
    created_at = Column(DateTime, default=datetime.utcnow)

class StaffPermission(Base):
    __tablename__ = "staff_permissions"

    id = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    staff_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permissions = Column(JSON, default=list)  # ["scan_tickets", "edit_event"]

class ReviewFlag(Base):
    __tablename__ = "review_flags"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, nullable=False)
    flag_reason = Column(String, nullable=False)
    status = Column(String, default="FLAGGED")  # FLAGGED, REMOVED, APPROVED

class Coupon(Base):
    __tablename__ = "coupons"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    discount_type = Column(String, default="PERCENTAGE")  # PERCENTAGE, FLAT
    discount_value = Column(Float, nullable=False)
    max_uses = Column(Integer, default=100)
    used_count = Column(Integer, default=0)
    expiry_date = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1 to 5
    comment = Column(Text, nullable=False)
    user_name = Column(String, default="Verified Attendee")
    created_at = Column(DateTime, default=datetime.utcnow)

