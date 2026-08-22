from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, index=True, default="Tech")
    location = Column(String, nullable=False)
    venue = Column(String, nullable=True)
    address = Column(String, nullable=True)
    start_time = Column(String, nullable=True)
    end_time = Column(String, nullable=True)
    date_str = Column(String, nullable=False)
    event_datetime = Column(DateTime, default=datetime.utcnow)
    price = Column(Float, nullable=False)
    total_capacity = Column(Integer, nullable=False, default=100)
    available_tickets = Column(Integer, nullable=False, default=100)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String, default="PUBLISHED")  # DRAFT, PUBLISHED, CANCELLED, PAST


    image_url = Column(String, nullable=True)
    cancellation_policy = Column(String, default="Standard 24-hour cancellation policy applies.")
    ticket_types = Column(JSON, default=list)
    max_tickets_per_booking = Column(Integer, default=10, nullable=True)
    lat = Column(Float, nullable=True)
    lng = Column(Float, nullable=True)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    tiers = relationship("TicketTier", back_populates="event", cascade="all, delete-orphan")



class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="CONFIRMED")  # RESERVED, CONFIRMED, CANCELLED, USED
    price_paid = Column(Float, nullable=False)
    qr_code_path = Column(String, nullable=True)
    checked_in_at = Column(DateTime, nullable=True)
    staff_id = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ScanLog(Base):
    __tablename__ = "scan_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    ticket_number = Column(String, nullable=True)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=True)
    staff_id = Column(String, default="#STAFF-001")
    result = Column(String, nullable=False)  # VALID, ALREADY_USED, CANCELLED, INVALID
    scanned_at = Column(DateTime, default=datetime.utcnow)

