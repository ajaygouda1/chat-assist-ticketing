from enum import Enum
from typing import List
from fastapi import HTTPException
from app.models.ticket import Event

class EventStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_REVIEW = "PENDING_REVIEW"
    PUBLISHED = "PUBLISHED"
    SALES_OPEN = "SALES_OPEN"
    SALES_CLOSED = "SALES_CLOSED"
    LIVE = "LIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"

VALID_EVENT_TRANSITIONS = {
    EventStatus.DRAFT: [EventStatus.PENDING_REVIEW, EventStatus.PUBLISHED, EventStatus.CANCELLED],
    EventStatus.PENDING_REVIEW: [EventStatus.PUBLISHED, EventStatus.DRAFT, EventStatus.CANCELLED],
    EventStatus.PUBLISHED: [EventStatus.SALES_OPEN, EventStatus.LIVE, EventStatus.CANCELLED, EventStatus.SUSPENDED],
    EventStatus.SALES_OPEN: [EventStatus.SALES_CLOSED, EventStatus.LIVE, EventStatus.CANCELLED, EventStatus.SUSPENDED],
    EventStatus.SALES_CLOSED: [EventStatus.LIVE, EventStatus.CANCELLED],
    EventStatus.LIVE: [EventStatus.COMPLETED, EventStatus.CANCELLED],
    EventStatus.COMPLETED: [],
    EventStatus.CANCELLED: [],
    EventStatus.SUSPENDED: [EventStatus.PUBLISHED, EventStatus.DRAFT, EventStatus.CANCELLED]
}

def transition_event_status(event: Event, target_status: str) -> str:
    current = event.status or "DRAFT"
    target = target_status.upper()

    if target not in [s.value for s in EventStatus]:
        raise HTTPException(status_code=400, detail=f"Invalid target event status '{target_status}'")

    if current == target:
        return target

    allowed = [s.value for s in VALID_EVENT_TRANSITIONS.get(EventStatus(current), [])]
    if target not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status transition from '{current}' to '{target}'. Allowed transitions: {allowed}"
        )

    # Required field validation before publishing
    if target == EventStatus.PUBLISHED.value:
        missing = []
        if not event.title or len(event.title.strip()) < 3:
            missing.append("Title")
        if not event.location or len(event.location.strip()) < 3:
            missing.append("Location")
        if event.price is None or event.price < 0:
            missing.append("Price")
        if not event.total_capacity or event.total_capacity <= 0:
            missing.append("Capacity")
        if missing:
            raise HTTPException(status_code=400, detail=f"Cannot publish event missing required fields: {', '.join(missing)}")

    if target == EventStatus.CANCELLED.value:
        from app.models.ticket_tier import TicketTier
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            tiers = db.query(TicketTier).filter(TicketTier.event_id == event.id).all()
            for t in tiers:
                if t.held_quantity > 0:
                    t.available_quantity += t.held_quantity
                    t.held_quantity = 0
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()

    event.status = target
    return target

