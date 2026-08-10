from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from datetime import datetime
from app.core.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(String, unique=True, index=True, nullable=False)
    order_id = Column(String, unique=True, nullable=False)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, default="INR")
    status = Column(String, default="SUCCESS")  # PENDING, SUCCESS, FAILED, REFUNDED, DISPUTED
    idempotency_key = Column(String, nullable=True, index=True)
    escrow_release_at = Column(DateTime, nullable=True)
    invoice_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
