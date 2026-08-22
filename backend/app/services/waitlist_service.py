from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional
from app.models.waitlist import WaitlistEntry
from app.models.notification import Notification

def join_waitlist(db: Session, event_id: int, user_id: int, ticket_tier: str = "Standard", quantity: int = 1) -> WaitlistEntry:
    # Check if user already on waitlist
    existing = db.query(WaitlistEntry).filter(
        WaitlistEntry.event_id == event_id,
        WaitlistEntry.user_id == user_id,
        WaitlistEntry.status == "WAITING"
    ).first()
    if existing:
        return existing

    # Calculate position
    count = db.query(WaitlistEntry).filter(
        WaitlistEntry.event_id == event_id,
        WaitlistEntry.status == "WAITING"
    ).count()

    entry = WaitlistEntry(
        event_id=event_id,
        ticket_tier=ticket_tier,
        user_id=user_id,
        requested_quantity=quantity,
        position=count + 1,
        status="WAITING"
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry

def process_waitlist_on_inventory_release(db: Session, event_id: int):
    """
    Notifies the top waitlisted customer when inventory frees up, giving them a 15-minute purchase deadline.
    """
    now = datetime.utcnow()
    # Expire old notifications first
    expired = db.query(WaitlistEntry).filter(
        WaitlistEntry.event_id == event_id,
        WaitlistEntry.status == "NOTIFIED",
        WaitlistEntry.purchase_deadline < now
    ).all()
    for exp in expired:
        exp.status = "EXPIRED"
    db.commit()

    # Get next in line
    next_entry = db.query(WaitlistEntry).filter(
        WaitlistEntry.event_id == event_id,
        WaitlistEntry.status == "WAITING"
    ).order_by(WaitlistEntry.position.asc()).first()

    if next_entry:
        next_entry.status = "NOTIFIED"
        next_entry.notified_at = now
        next_entry.purchase_deadline = now + timedelta(minutes=15)
        
        # Send in-app notification
        notif = Notification(
            user_id=next_entry.user_id,
            type="EVENTS",
            title="Ticket Available from Waitlist!",
            message=f"A ticket for Event #{event_id} is now available for you to purchase. Claim within 15 minutes!",
            metadata_json={"event_id": event_id, "waitlist_id": next_entry.id}
        )
        db.add(notif)
        db.commit()
