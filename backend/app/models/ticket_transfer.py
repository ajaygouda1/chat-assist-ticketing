from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base

class TicketTransfer(Base):
    __tablename__ = "ticket_transfers"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    from_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    to_user_email = Column(String, nullable=False)
    to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="PENDING")  # PENDING, ACCEPTED, REJECTED, CANCELLED
    old_ticket_number = Column(String, nullable=False)
    new_ticket_number = Column(String, nullable=True)
    requested_at = Column(DateTime, default=datetime.utcnow)
    transferred_at = Column(DateTime, nullable=True)
