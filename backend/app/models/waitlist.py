from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from datetime import datetime
from app.core.database import Base

class WaitlistEntry(Base):
    __tablename__ = "waitlist_entries"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    ticket_tier = Column(String, default="Standard")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    requested_quantity = Column(Integer, default=1)
    joined_timestamp = Column(DateTime, default=datetime.utcnow)
    position = Column(Integer, default=1)
    status = Column(String, default="WAITING")  # WAITING, NOTIFIED, PURCHASED, EXPIRED, CANCELLED
    notified_at = Column(DateTime, nullable=True)
    purchase_deadline = Column(DateTime, nullable=True)
