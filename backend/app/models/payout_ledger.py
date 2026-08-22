from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from datetime import datetime
from app.core.database import Base

class PayoutLedger(Base):
    __tablename__ = "payout_ledgers"

    id = Column(Integer, primary_key=True, index=True)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    gross_sales = Column(Float, default=0.0)
    refunds_total = Column(Float, default=0.0)
    platform_fee = Column(Float, default=0.0)
    payment_processing_fee = Column(Float, default=0.0)
    net_payout = Column(Float, default=0.0)
    status = Column(String, default="PENDING")  # PENDING, SCHEDULED, PROCESSING, PAID, FAILED
    payout_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
