from sqlalchemy.orm import Session
from datetime import datetime
from typing import Tuple
from fastapi import HTTPException
from app.models.ticket import Ticket, Event
from app.models.refund import RefundPolicy, RefundRequest
from app.models.seating import Seat
from app.services.waitlist_service import process_waitlist_on_inventory_release

def calculate_refund_amount(db: Session, ticket: Ticket, event: Event) -> Tuple[float, str]:
    """
    Calculates eligible refund percentage based on time window before event start.
    """
    policy = db.query(RefundPolicy).filter(RefundPolicy.event_id == event.id).first()
    policy_type = policy.policy_type if policy else "FLEXIBLE"

    if policy_type == "NON_REFUNDABLE":
        return 0.0, "Event policy is non-refundable."

    # Parse date string or use event_datetime
    event_time = event.event_datetime or datetime.utcnow()
    hours_left = (event_time - datetime.utcnow()).total_seconds() / 3600.0

    if policy_type == "FLEXIBLE":
        if hours_left >= 168:  # 7 days
            return round(ticket.price_paid * 1.0, 2), "100% refund (> 7 days before event)"
        elif hours_left >= 72:  # 3-7 days
            return round(ticket.price_paid * 0.75, 2), "75% refund (3-7 days before event)"
        elif hours_left >= 24:  # 24-72 hrs
            return round(ticket.price_paid * 0.50, 2), "50% refund (24-72 hours before event)"
        else:
            return 0.0, "No refund (< 24 hours before event)"
    elif policy_type == "MODERATE":
        if hours_left >= 168:
            return round(ticket.price_paid * 1.0, 2), "100% refund (> 7 days before event)"
        elif hours_left >= 72:
            return round(ticket.price_paid * 0.50, 2), "50% refund (3-7 days before event)"
        else:
            return 0.0, "No refund (< 72 hours before event)"
    elif policy_type == "STRICT":
        if hours_left >= 168:
            return round(ticket.price_paid * 0.50, 2), "50% refund (> 7 days before event)"
        else:
            return 0.0, "No refund (< 7 days before event)"
    else:  # Custom or default
        if hours_left >= 24:
            return round(ticket.price_paid * 0.80, 2), "80% refund policy applies"
        return 0.0, "No refund (< 24 hours before event)"

def approve_refund(db: Session, refund_req: RefundRequest, reviewer_id: int):
    """
    Approves refund: invalidates ticket, restores exact quantity to tier, releases reserved seats, triggers waitlist.
    Includes idempotency guard to prevent double restoration.
    """
    if refund_req.inventory_restored == 1:
        # Already restored inventory, return immediately to ensure idempotency
        return

    ticket = db.query(Ticket).filter(Ticket.id == refund_req.ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    qty_to_refund = refund_req.quantity_refunded or 1

    ticket.status = "REFUNDED"
    refund_req.status = "REFUNDED"
    refund_req.reviewed_by_user_id = reviewer_id
    refund_req.processed_at = datetime.utcnow()
    refund_req.inventory_restored = 1

    # Free up physical seats if reserved
    seats = db.query(Seat).filter(Seat.ticket_id == ticket.id).all()
    for seat in seats:
        seat.status = "AVAILABLE"
        seat.ticket_id = None
        seat.held_by_user_id = None

    # Free capacity
    event = db.query(Event).filter(Event.id == ticket.event_id).first()
    if event:
        event.available_tickets += qty_to_refund

    # Free ticket tier inventory with exact quantity
    from app.models.ticket_tier import TicketTier
    tier = db.query(TicketTier).filter(TicketTier.event_id == ticket.event_id).first()
    if tier:
        actual_deduct = min(tier.sold_quantity, qty_to_refund)
        tier.sold_quantity = max(0, tier.sold_quantity - actual_deduct)
        tier.available_quantity += qty_to_refund

    db.commit()



    # Trigger waitlist allocation
    process_waitlist_on_inventory_release(db, ticket.event_id)
