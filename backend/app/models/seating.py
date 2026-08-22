from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON
from datetime import datetime
from app.core.database import Base

class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=True)
    city = Column(String, nullable=True)
    total_capacity = Column(Integer, default=100)
    layout_data = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)


class Section(Base):
    __tablename__ = "sections"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    name = Column(String, nullable=False)
    pricing_tier = Column(String, default="Standard")  # VIP, Gold, Standard
    price_multiplier = Column(Float, default=1.0)


class Seat(Base):
    __tablename__ = "seats"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    section_id = Column(Integer, ForeignKey("sections.id"), nullable=True)
    section_name = Column(String, default="Main Floor")
    row_label = Column(String, nullable=False)  # A, B, C...
    seat_number = Column(Integer, nullable=False)  # 1, 2, 3...
    seat_code = Column(String, index=True, nullable=False)  # A-1, A-2...
    status = Column(String, default="AVAILABLE", index=True)  # AVAILABLE, HELD, SOLD, BLOCKED
    price = Column(Float, nullable=False, default=0.0)
    held_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    held_until = Column(DateTime, nullable=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
