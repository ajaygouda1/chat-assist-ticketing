import uuid
import tempfile
import os
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional, Any
from datetime import datetime, timedelta

from app.core.database import get_db
from app.models.ticket import Event, Ticket, ScanLog
from app.models.payment import Payment
from app.models.user import User
from app.models.ml_models import FraudFlag
from app.schemas.schemas import (
    EventCreate, EventUpdate, EventResponse, BookingCreate, BookingResponse,
    VerifyRequest, CheckInRequest, TransferRequest
)
from app.ml.fraud_detector import fraud_detector

from app.services.gst_service import generate_gst_invoice_pdf
from app.services.qr_service import generate_ticket_qr_base64, verify_ticket_token, sign_ticket_token
from app.services.wallet_service import generate_google_wallet_link, generate_apple_wallet_link
from app.jobs.reservation_expiry import on_reservation_expired
from app.core.authorization import require_event_owner, get_current_user

router = APIRouter()


@router.get("/events", response_model=List[EventResponse])
def get_events(status: Optional[str] = Query("PUBLISHED"), db: Session = Depends(get_db)):
    query = db.query(Event)
    if status and status.upper() != "ALL":
        query = query.filter(Event.status == status.upper())
    return query.order_by(Event.id.desc()).all()

@router.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: int, db: Session = Depends(get_db)):
    ev = db.query(Event).filter(Event.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")
    return ev

@router.post("/events", response_model=EventResponse)
def create_event(
    event_in: EventCreate,
    current_user: Optional[User] = Depends(get_current_user),
    organizer_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    effective_organizer_id = organizer_id or (current_user.id if current_user else 1)
    max_per_order = event_in.max_tickets_per_booking or 10

    ev = Event(
        title=event_in.title,
        description=event_in.description,
        category=event_in.category or "Tech",
        location=event_in.location,
        venue=event_in.venue,
        address=event_in.address,
        start_time=event_in.start_time,
        end_time=event_in.end_time,
        date_str=event_in.date_str,
        price=event_in.price,
        total_capacity=event_in.total_capacity,
        available_tickets=event_in.total_capacity,
        max_tickets_per_booking=max_per_order,
        organizer_id=effective_organizer_id,
        status=event_in.status or "DRAFT",
        image_url=event_in.image_url or "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=600&auto=format&fit=crop&q=80",
        cancellation_policy=event_in.cancellation_policy or "Standard 24-hour cancellation policy applies.",
        ticket_types=event_in.ticket_types or [],
        lat=event_in.lat,
        lng=event_in.lng,
        tags=event_in.tags or []
    )
    db.add(ev)
    db.commit()
    db.refresh(ev)

    # Transactional Tier Creation (Requirement 7 & 8)
    tiers_to_create = event_in.ticket_types or []
    if not tiers_to_create:
        tiers_to_create = [{
            "name": "General",
            "price": ev.price,
            "total_quantity": ev.total_capacity,
            "min_per_order": 1,
            "max_per_order": max_per_order
        }]

    try:
        from app.services.tier_inventory_service import create_or_update_event_tiers
        create_or_update_event_tiers(db, ev, tiers_to_create)
    except Exception as e:
        db.delete(ev)
        db.commit()
        raise HTTPException(status_code=400, detail=f"Failed to create ticket tiers: {str(e)}")

    db.refresh(ev)
    return ev

@router.put("/events/{event_id}", response_model=EventResponse)
def update_event(event_id: int, event_in: EventUpdate, db: Session = Depends(get_db), owner_check: Event = Depends(require_event_owner)):
    ev = owner_check

    update_data = event_in.dict(exclude_unset=True)
    for field, val in update_data.items():
        if val is not None:
            setattr(ev, field, val)

    # Recalculate available tickets if total capacity was updated
    if "total_capacity" in update_data and update_data["total_capacity"] is not None:
        tickets_sold = db.query(Ticket).filter(Ticket.event_id == event_id, Ticket.status != "CANCELLED").count()
        ev.available_tickets = max(0, ev.total_capacity - tickets_sold)

    if "ticket_types" in update_data and update_data["ticket_types"]:
        from app.services.tier_inventory_service import create_or_update_event_tiers
        create_or_update_event_tiers(db, ev, update_data["ticket_types"])

    db.commit()
    db.refresh(ev)
    return ev


@router.post("/events/{event_id}/publish")
def publish_event(event_id: int, db: Session = Depends(get_db), owner_check: Event = Depends(require_event_owner)):
    ev = owner_check

    # Section 45d Validation Rules prior to publishing:
    errors = []

    if not ev.title or len(ev.title.strip()) < 3:
        errors.append("Title must be at least 3 characters long.")
    
    if not ev.description or len(ev.description.strip()) < 10:
        errors.append("Description must be detailed (at least 10 characters).")

    if not ev.location or not ev.date_str:
        errors.append("Event date and location are required.")

    if not ev.image_url or not ev.image_url.strip():
        ev.image_url = "https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=800&auto=format&fit=crop&q=80"

    if ev.price < 0:
        errors.append("Ticket price cannot be negative.")

    if ev.total_capacity <= 0:
        errors.append("Total capacity must be greater than 0.")

    if ev.ticket_types and isinstance(ev.ticket_types, list) and len(ev.ticket_types) > 0:
        total_type_capacity = sum(int(t.get("total_quantity") or t.get("quantity") or 0) for t in ev.ticket_types)
        if ev.total_capacity < total_type_capacity:
            errors.append(f"Total capacity ({ev.total_capacity}) must be >= sum of ticket tiers ({total_type_capacity}).")

    if errors:
        raise HTTPException(status_code=400, detail={"message": "Validation failed on publish", "errors": errors})

    # Ensure ticket_tiers table contains at least one default General tier upon publish
    from app.models.ticket_tier import TicketTier
    existing_tiers = db.query(TicketTier).filter(TicketTier.event_id == ev.id).all()
    if not existing_tiers:
        from app.services.tier_inventory_service import create_or_update_event_tiers
        create_or_update_event_tiers(db, ev, [{
            "name": "General",
            "price": ev.price,
            "total_quantity": ev.total_capacity,
            "min_per_order": 1,
            "max_per_order": ev.max_tickets_per_booking or 10
        }])

    ev.status = "PUBLISHED"
    db.commit()
    db.refresh(ev)
    return {"status": "PUBLISHED", "message": f"'{ev.title}' is now live and published!", "event": ev}

@router.post("/events/{event_id}/duplicate")
def duplicate_event(event_id: int, db: Session = Depends(get_db), owner_check: Event = Depends(require_event_owner)):
    original = owner_check

    cloned = Event(
        title=f"{original.title} (Copy)",
        description=original.description,
        category=original.category,
        location=original.location,
        venue=original.venue,
        address=original.address,
        start_time=original.start_time,
        end_time=original.end_time,
        date_str=original.date_str,
        price=original.price,
        total_capacity=original.total_capacity,
        available_tickets=original.total_capacity,
        organizer_id=original.organizer_id,
        status="DRAFT",
        image_url=original.image_url,
        cancellation_policy=original.cancellation_policy,
        ticket_types=original.ticket_types,
        lat=original.lat,
        lng=original.lng,
        tags=original.tags or []
    )
    db.add(cloned)
    db.commit()
    db.refresh(cloned)
    return cloned

@router.post("/events/{event_id}/cancel")
def cancel_event(event_id: int, db: Session = Depends(get_db), owner_check: Event = Depends(require_event_owner)):
    ev = owner_check

    ev.status = "CANCELLED"
    db.commit()
    return {"status": "CANCELLED", "message": f"Event '{ev.title}' has been cancelled."}


@router.post("/book", response_model=BookingResponse)
def book_ticket(
    booking_in: BookingCreate,
    current_user: Optional[User] = Depends(get_current_user),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    effective_user_id = (current_user.id if current_user else None) or user_id or 1

    ev = db.query(Event).filter(Event.id == booking_in.event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    if ev.status != "PUBLISHED":
        raise HTTPException(status_code=400, detail="Event is not published for booking")

    from app.models.ticket_tier import TicketTier
    tier_query = db.query(TicketTier).filter(TicketTier.event_id == ev.id)
    if booking_in.tier_id:
        tier = tier_query.filter(TicketTier.id == booking_in.tier_id).first()
    elif booking_in.ticket_type:
        tier = tier_query.filter(TicketTier.name.ilike(f"%{booking_in.ticket_type}%")).first()
    else:
        tier = None

    if not tier:
        tier = tier_query.first()

    if not tier:
        raise HTTPException(status_code=400, detail="No valid ticket tier available for this event.")

    if booking_in.quantity < tier.min_per_order:
        raise HTTPException(status_code=400, detail=f"Minimum order quantity for '{tier.name}' is {tier.min_per_order}.")

    if booking_in.quantity > tier.max_per_order:
        raise HTTPException(status_code=400, detail=f"Maximum order quantity for '{tier.name}' is {tier.max_per_order}.")

    if booking_in.quantity > tier.available_quantity:
        raise HTTPException(status_code=400, detail="Not enough tickets available or sold out.")

    from decimal import Decimal, ROUND_HALF_UP
    from app.models.booking_draft import BookingDraft
    
    unit_price = Decimal(str(tier.price))
    subtotal = unit_price * Decimal(str(booking_in.quantity))

    discount = Decimal("0.0")
    if booking_in.coupon_code:
        from app.models.promo import PromoCode
        promo = db.query(PromoCode).filter(PromoCode.code == booking_in.coupon_code.upper()).first()
        if promo and promo.is_active:
            if promo.discount_type == "PERCENTAGE":
                discount = (subtotal * Decimal(str(promo.discount_value))) / Decimal("100")
            else:
                discount = Decimal(str(promo.discount_value))
            if promo.max_discount_amount:
                discount = min(discount, Decimal(str(promo.max_discount_amount)))

    taxable = max(Decimal("0.0"), subtotal - discount)
    tax = (taxable * Decimal("0.18")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    total = (taxable + tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Check idempotency
    if booking_in.idempotency_key:
        existing_draft = db.query(BookingDraft).filter(BookingDraft.idempotency_key == booking_in.idempotency_key).first()
        if existing_draft:
            return {
                "booking_id": existing_draft.id,
                "event_title": ev.title,
                "price_paid": existing_draft.total,
                "status": existing_draft.status
            }

    # Hold inventory in TicketTier
    from app.services.tier_inventory_service import hold_tier_inventory
    hold_tier_inventory(db, ev.id, tier.id, booking_in.quantity, effective_user_id)

    draft_number = f"DFT-{uuid.uuid4().hex[:8].upper()}"
    draft = BookingDraft(
        draft_number=draft_number,
        user_id=effective_user_id,
        event_id=ev.id,
        ticket_type=tier.name,
        quantity=booking_in.quantity,
        unit_price=float(unit_price),
        subtotal=float(subtotal),
        tax=float(tax),
        total=float(total),
        idempotency_key=booking_in.idempotency_key,
        status="HELD",
        expires_at=datetime.utcnow() + timedelta(minutes=10)
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)

    # Zero payment / free event completion
    if total == Decimal("0.0"):
        from app.services.payment_service import confirm_payment
        res = confirm_payment(
            order_id=f"free_ord_{draft.id}",
            payment_id=f"free_pay_{draft.id}",
            signature="free_event_trusted",
            source="free_booking",
            booking_id=draft.id,
            user_id=effective_user_id,
            db=db
        )
        return {
            "booking_id": draft.id,
            "ticket_id": res.get("ticket", {}).get("id"),
            "ticket_number": res.get("ticket", {}).get("ticket_number"),
            "event_title": ev.title,
            "price_paid": 0.0,
            "status": "CONFIRMED",
            "invoice_number": res.get("invoice_number"),
            "qr_code_url": res.get("ticket", {}).get("qr_code_url"),
            "tickets": res.get("tickets")
        }

    return {
        "booking_id": draft.id,
        "event_title": ev.title,
        "price_paid": draft.total,
        "status": "HELD"
    }

@router.get("/user/tickets")
def get_user_tickets(
    current_user: Optional[User] = Depends(get_current_user),
    user_id: Optional[int] = Query(None),
    db: Session = Depends(get_db)
):
    effective_user_id = (current_user.id if current_user else None) or user_id or 1
    tickets = db.query(Ticket).filter(Ticket.user_id == effective_user_id).order_by(Ticket.id.desc()).all()
    results = []
    for t in tickets:
        ev = db.query(Event).filter(Event.id == t.event_id).first()
        payment = db.query(Payment).filter(Payment.user_id == t.user_id).order_by(Payment.id.desc()).first()
        payment_id = payment.payment_id if payment else "pay_sample"
        token, qr_data_url = generate_ticket_qr_base64(str(t.id), payment_id, str(ev.id if ev else 1))

        results.append({
            "id": t.id,
            "ticket_number": t.ticket_number,
            "event_id": t.event_id,
            "event_title": ev.title if ev else "Event",
            "date_str": ev.date_str if ev else "",
            "location": ev.location if ev else "",
            "price_paid": round(t.price_paid or 0.0, 2),
            "status": t.status,
            "qr_token": token,
            "qr_data_url": qr_data_url,
            "created_at": t.created_at
        })
    return results


@router.post("/tickets/verify")
def verify_ticket(
    req: Optional[VerifyRequest] = None,
    qr_token: Optional[str] = Query(None),
    ticket_number: Optional[str] = Query(None),
    event_id: Optional[Any] = Query(None),
    db: Session = Depends(get_db)
):
    token_val = req.qr_token if req and req.qr_token else (qr_token if isinstance(qr_token, str) else "")
    number_val = req.ticket_number if req and req.ticket_number else (ticket_number if isinstance(ticket_number, str) else "")
    raw_event_id = req.event_id if req and req.event_id is not None else (event_id if isinstance(event_id, (int, str)) else None)

    target_event_id = None
    if raw_event_id is not None:
        raw_str = str(raw_event_id).strip().upper()
        if raw_str not in ["", "0", "NONE", "NULL", "ALL", "ALL EVENTS", "ALL EVENTS (NO SCOPE FILTER)"]:
            try:
                val = int(raw_str)
                if val > 0:
                    target_event_id = val
            except (ValueError, TypeError):
                target_event_id = None

    token_clean = (token_val or "").strip()
    number_clean = (number_val or "").strip()

    ticket = None

    # First attempt signed HMAC token verification (§46 & §47)
    if token_clean:
        decoded = verify_ticket_token(token_clean)
        if decoded and "ticket_id" in decoded:
            try:
                ticket = db.query(Ticket).filter(Ticket.id == int(decoded["ticket_id"])).first()
                # §57d token re-signing check: If ticket was re-signed, old token fails
                if ticket and ticket.qr_code_path and ticket.qr_code_path != token_clean:
                    ticket = None
            except (ValueError, TypeError):
                ticket = None
        
        if not ticket:
            # Fallback: check if raw string matches ticket_number or qr_code_path directly
            ticket = db.query(Ticket).filter(
                (Ticket.ticket_number == token_clean.upper()) |
                (Ticket.qr_code_path == token_clean)
            ).first()


    elif number_clean:
        ticket = db.query(Ticket).filter(Ticket.ticket_number == number_clean.upper()).first()

    # Log scan attempt
    scan_log = ScanLog(
        ticket_id=ticket.id if ticket else None,
        ticket_number=ticket.ticket_number if ticket else (number_clean or token_clean[:20]),
        event_id=target_event_id or (ticket.event_id if ticket else None),
        staff_id="#GATE-STAFF-1",
        result="INVALID"
    )

    if not ticket:
        scan_log.result = "INVALID"
        db.add(scan_log)
        db.commit()
        return {"valid": False, "status": "INVALID", "message": "❌ Invalid Ticket Token or Not Found"}

    ev = db.query(Event).filter(Event.id == ticket.event_id).first()

    # Optional event scope check: Only enforce when a specific positive event_id is selected (§47)
    is_scoped = target_event_id is not None and target_event_id > 0
    if is_scoped and int(ticket.event_id) != target_event_id:
        scan_log.result = "INVALID_EVENT"
        db.add(scan_log)
        db.commit()
        return {
            "valid": False,
            "status": "INVALID_EVENT",
            "message": f"❌ Ticket is for a different event ('{ev.title if ev else 'Other'}')",
            "ticket": {"id": ticket.id, "ticket_number": ticket.ticket_number, "status": ticket.status}
        }


    status_upper = (ticket.status or "").upper()
    if status_upper in ["USED", "CHECKED_IN"]:
        scan_log.result = "ALREADY_USED"
        db.add(scan_log)
        db.commit()
        return {
            "valid": False,
            "status": "ALREADY_USED",
            "message": "❌ Ticket Already Checked In!",
            "checked_in_at": ticket.checked_in_at,
            "ticket": {"id": ticket.id, "ticket_number": ticket.ticket_number, "status": ticket.status},
            "event_title": ev.title if ev else ""
        }

    if status_upper in ["CANCELLED", "REFUNDED", "TRANSFERRED"]:
        scan_log.result = status_upper
        db.add(scan_log)
        db.commit()
        return {
            "valid": False,
            "status": "CANCELLED_OR_REFUNDED",
            "message": f"❌ Ticket Invalid ({status_upper})",
            "ticket": {"id": ticket.id, "ticket_number": ticket.ticket_number, "status": ticket.status},
            "event_title": ev.title if ev else ""
        }


    scan_log.result = "VALID"
    db.add(scan_log)
    db.commit()

    return {
        "valid": True,
        "status": "CONFIRMED",
        "message": f"✅ Valid Pass for {ev.title if ev else 'Event'}",
        "ticket": {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "event_id": ticket.event_id,
            "status": ticket.status,
            "price_paid": ticket.price_paid
        },
        "ticket_number": ticket.ticket_number,
        "event_title": ev.title if ev else "",
        "seat": "General Admission / VIP",
        "price_paid": ticket.price_paid
    }

@router.post("/tickets/{ticket_id}/check-in")
@router.post("/tickets/check-in")
def check_in_ticket(
    ticket_id: Optional[int] = None,
    ticket_number: Optional[str] = Query(None),
    req: Optional[CheckInRequest] = None,
    db: Session = Depends(get_db)
):
    target_id = req.ticket_id if req and req.ticket_id else (ticket_id if isinstance(ticket_id, (int, str)) else None)
    target_number = req.ticket_number if req and req.ticket_number else (ticket_number if isinstance(ticket_number, str) else None)
    staff_id = (req.staff_id if req and req.staff_id else (ticket_number if isinstance(ticket_number, str) else None)) or "#GATE-STAFF-1"


    query = db.query(Ticket)
    if target_id:
        query = query.filter(Ticket.id == int(target_id))
    elif target_number:
        query = query.filter(Ticket.ticket_number == target_number.strip().upper())
    else:
        raise HTTPException(status_code=400, detail="Must provide ticket_id or ticket_number")

    ticket = query.first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    status_upper = (ticket.status or "").upper()
    if status_upper in ["USED", "CHECKED_IN"]:
        return {
            "success": True,
            "status": "CHECKED_IN",
            "message": "Ticket was already checked in (idempotent confirm)",
            "ticket": {"id": ticket.id, "ticket_number": ticket.ticket_number, "status": "CHECKED_IN"}
        }

    if status_upper == "CANCELLED":
        raise HTTPException(status_code=400, detail="Cannot check in cancelled ticket")

    ticket.status = "CHECKED_IN"
    ticket.checked_in_at = datetime.utcnow()
    ticket.staff_id = staff_id

    scan_log = ScanLog(
        ticket_id=ticket.id,
        ticket_number=ticket.ticket_number,
        event_id=ticket.event_id,
        staff_id=staff_id,
        result="CHECKED_IN"
    )
    db.add(scan_log)
    db.commit()

    ev = db.query(Event).filter(Event.id == ticket.event_id).first()
    return {
        "success": True,
        "status": "CHECKED_IN",
        "message": f"Welcome! Checked in for {ev.title if ev else 'Event'}",
        "ticket": {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "status": "CHECKED_IN"
        }
    }

@router.get("/tickets/{ticket_id}/wallet")
def get_ticket_wallet_links(ticket_id: int, db: Session = Depends(get_db)):
    """
    Wallet Passes:
    Generates Google Wallet save link and Apple Wallet pass link for a given ticket.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    event = db.query(Event).filter(Event.id == ticket.event_id).first()
    payment = db.query(Payment).filter(Payment.ticket_id == ticket.id).first()
    payment_id = payment.payment_id if payment else "pay_sample"
    token, _ = generate_ticket_qr_base64(str(ticket.id), payment_id, str(event.id if event else 1))

    ticket_data = {
        "id": ticket.id,
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "event_title": event.title if event else "ChatAssist Live Event",
        "user_name": "Valued Attendee",
        "ticket_token": token,
        "qr_token": token
    }

    g_wallet_url = generate_google_wallet_link(ticket_data)
    a_wallet_url = generate_apple_wallet_link(ticket_data)

    return {
        "ticket_id": ticket.id,
        "google_wallet_url": g_wallet_url,
        "apple_wallet_url": a_wallet_url
    }


@router.post("/tickets/{ticket_id}/transfer")
def transfer_ticket(
    ticket_id: int,
    payload: TransferRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ticket Transfer / Gifting:
    Transfers ticket ownership to a new recipient email and re-signs the HMAC token
    so that any old QR codes or screenshots immediately fail verification.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    status_upper = (ticket.status or "").upper()
    if status_upper not in ["CONFIRMED", "ACTIVE"]:
        raise HTTPException(
            status_code=400,
            detail="Only active, confirmed tickets can be transferred"
        )

    # Check recipient user
    recipient_email = payload.recipient_email.strip().lower()
    new_owner = db.query(User).filter(User.email == recipient_email).first()
    if not new_owner:
        # Create recipient user if not already present
        new_owner = User(
            email=recipient_email,
            name=recipient_email.split("@")[0].title(),
            hashed_password="social_transfer_dummy",
            role="customer"
        )

        db.add(new_owner)
        db.flush()

    payment = db.query(Payment).filter(Payment.ticket_id == ticket.id).first()
    payment_id = payment.payment_id if payment else f"pay_transfer_{uuid.uuid4().hex[:6]}"

    # Re-sign HMAC token: previous QR code screenshot becomes invalid
    new_qr_token, new_qr_b64 = generate_ticket_qr_base64(str(ticket.id), payment_id, str(ticket.event_id))
    
    ticket.user_id = new_owner.id
    ticket.qr_code_path = new_qr_token
    ticket.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(ticket)

    return {
        "success": True,
        "message": f"Ticket #{ticket.ticket_number} successfully transferred to {recipient_email}. Previous QR code is invalidated.",
        "ticket": {
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "status": ticket.status,
            "new_owner_email": new_owner.email,
            "qr_token": new_qr_token,
            "qr_code_url": new_qr_b64
        }
    }


@router.post("/bookings/{booking_id}/expire")
def expire_abandoned_booking(booking_id: int, db: Session = Depends(get_db)):
    """
    Abandoned Booking Recovery endpoint:
    Triggers reservation expiration, releases reserved tickets back to available inventory, and schedules recovery nudge.
    """
    res = on_reservation_expired(booking_id, db)
    return res





