from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base

class Gate(Base):
    __tablename__ = "gates"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    name = Column(String, nullable=False)  # Gate A, Gate B, VIP Gate, Staff Gate
    location_note = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
