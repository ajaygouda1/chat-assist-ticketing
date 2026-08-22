from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class TicketTier(Base):
    __tablename__ = "ticket_tiers"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False, index=True)
    name = Column(String, nullable=False)  # e.g. "VIP Pass", "Gold Pass", "Standard Pass"
    price = Column(Float, nullable=False, default=0.0)
    total_quantity = Column(Integer, nullable=False, default=50)
    available_quantity = Column(Integer, nullable=False, default=50)
    held_quantity = Column(Integer, nullable=False, default=0)
    sold_quantity = Column(Integer, nullable=False, default=0)
    min_per_order = Column(Integer, nullable=False, default=1)
    max_per_order = Column(Integer, nullable=False, default=10)
    sales_start = Column(DateTime, nullable=True)
    sales_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="tiers")
