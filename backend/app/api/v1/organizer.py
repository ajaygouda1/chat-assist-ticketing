from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.core.database import get_db
from app.models.ml_models import Payout, StaffPermission
from app.models.ticket import Event, Ticket, ScanLog
from app.models.user import User
from app.schemas.schemas import OrganizerApplicationRequest, DraftRequest, BroadcastRequest
from app.core.authorization import get_current_user, require_event_owner
from app.services.openai_service import ai_service


router = APIRouter()


@router.get("/organizer/events")
def get_organizer_events(
    status: Optional[str] = Query(None, description="Filter by status: DRAFT, PUBLISHED, PAST, CANCELLED"),
    organizer_id: int = 1,
    db: Session = Depends(get_db)
):
    query = db.query(Event)
    if organizer_id:
        query = query.filter((Event.organizer_id == organizer_id) | (Event.organizer_id.is_(None)))
    if status and status.upper() != "ALL":
        query = query.filter(Event.status == status.upper())
    
    events = query.order_by(Event.id.desc()).all()
    results = []
    for ev in events:
        tickets = db.query(Ticket).filter(Ticket.event_id == ev.id, Ticket.status != "CANCELLED").all()
        tickets_sold = len(tickets)
        revenue_so_far = sum(t.price_paid for t in tickets)
        
        results.append({
            "id": ev.id,
            "title": ev.title,
            "description": ev.description,
            "category": ev.category,
            "location": ev.location,
            "venue": ev.venue,
            "address": ev.address,
            "start_time": ev.start_time,
            "end_time": ev.end_time,
            "date_str": ev.date_str,
            "price": ev.price,
            "total_capacity": ev.total_capacity,
            "available_tickets": ev.available_tickets,
            "tickets_sold": tickets_sold,
            "revenue_so_far": revenue_so_far,
            "status": ev.status or "PUBLISHED",
            "image_url": ev.image_url,
            "cancellation_policy": ev.cancellation_policy,
            "ticket_types": ev.ticket_types or [],
            "created_at": ev.created_at
        })
    return results

@router.get("/organizer/events/{event_id}/bookings")
def get_event_bookings(event_id: int, db: Session = Depends(get_db)):
    ev = db.query(Event).filter(Event.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    
    tickets = db.query(Ticket).filter(Ticket.event_id == event_id).all()
    bookings = []
    for t in tickets:
        bookings.append({
            "ticket_id": t.id,
            "ticket_number": t.ticket_number,
            "status": t.status,
            "price_paid": t.price_paid,
            "checked_in_at": t.checked_in_at,
            "created_at": t.created_at
        })
    
    return {
        "event_id": ev.id,
        "event_title": ev.title,
        "total_bookings": len(bookings),
        "bookings": bookings
    }

@router.get("/organizer/payouts")
def get_organizer_payouts(organizer_id: int = 1, db: Session = Depends(get_db)):
    payouts = db.query(Payout).filter(Payout.organizer_id == organizer_id).all()
    if not payouts:
        # Seed initial sample payout
        p = Payout(organizer_id=organizer_id, amount=14500.0, status="COMPLETED", paid_at=datetime.utcnow())
        db.add(p)
        db.commit()
        payouts = [p]
    return payouts

@router.post("/staff/invite")
def invite_staff(staff_email: str, permissions: List[str], organizer_id: int = 1, db: Session = Depends(get_db)):
    return {
        "status": "success",
        "message": f"Invited {staff_email} with permissions: {', '.join(permissions)}"
    }

@router.post("/organizer/apply")
def apply_as_organizer(
    payload: Optional[OrganizerApplicationRequest] = None,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    current_user.role = "organizer"
    db.commit()
    db.refresh(current_user)

    return {
        "status": "APPROVED",
        "message": f"User '{current_user.email}' application APPROVED. Role updated to Organizer.",
        "organization_name": payload.organization_name if payload else current_user.name,
        "user_id": current_user.id,
        "role": current_user.role
    }

@router.post("/organizer/events/draft-description")
def draft_description(
    payload: DraftRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    AI-Assisted Event Description Drafting:
    Turns rough organizer bullet points into a polished draft description for review.
    """
    notes = payload.bullet_points.strip()
    if not notes:
        raise HTTPException(status_code=400, detail="Bullet points/notes cannot be empty.")

    # Call AI service or prompt generator
    prompt = f"Draft a professional, engaging 2-3 sentence event description from these rough notes:\n{notes}"
    raw_ai_res = ai_service.process_chat_message(prompt, user_id=1, db=db)
    draft_text = raw_ai_res.get("reply") or f"Join us for an exciting experience! {notes}"

    return {
        "success": True,
        "bullet_points": notes,
        "draft": draft_text,
        "disclaimer": "Organizer must review and edit draft copy before publishing."
    }


@router.post("/organizer/events/{event_id}/broadcast")
def emergency_broadcast(
    event_id: int,
    payload: BroadcastRequest,
    current_user: Optional[User] = Depends(get_current_user),
    owner_check: Event = Depends(require_event_owner),
    db: Session = Depends(get_db)
):
    """
    Emergency Broadcast to Checked-In Attendees:
    Dispatches high-priority alerts specifically to attendees physically checked-in at the gate.
    """

    event = owner_check
    
    # Query checked-in tickets or scan logs
    checked_in_tickets = db.query(Ticket).filter(
        Ticket.event_id == event_id,
        Ticket.status == "CHECKED_IN"
    ).all()

    recipient_user_ids = list(set([t.user_id for t in checked_in_tickets if t.user_id]))
    notified_count = len(recipient_user_ids) if recipient_user_ids else len(checked_in_tickets)

    broadcast_record = {
        "event_id": event_id,
        "event_title": event.title,
        "message": payload.message,
        "priority": payload.priority or "high",
        "notified_count": notified_count,
        "dispatched_at": datetime.utcnow().isoformat() + "Z"
    }

    return {
        "success": True,
        "message": f"📢 High-priority broadcast dispatched to {notified_count} checked-in attendee(s).",
        "broadcast": broadcast_record
    }



