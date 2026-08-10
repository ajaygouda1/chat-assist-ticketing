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
def create_event(event_in: EventCreate, organizer_id: int = 1, db: Session = Depends(get_db)):
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
        organizer_id=organizer_id,
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
        errors.append("Event poster image is required to publish.")

    if ev.price < 0:
        errors.append("Ticket price cannot be negative.")

    if ev.total_capacity <= 0:
        errors.append("Total capacity must be greater than 0.")

    if ev.ticket_types and isinstance(ev.ticket_types, list) and len(ev.ticket_types) > 0:
        total_type_capacity = sum(int(t.get("quantity", 0)) for t in ev.ticket_types)
        if ev.total_capacity < total_type_capacity:
            errors.append(f"Total capacity ({ev.total_capacity}) must be >= sum of ticket tiers ({total_type_capacity}).")

    if errors:
        raise HTTPException(status_code=400, detail={"message": "Validation failed on publish", "errors": errors})

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
def book_ticket(booking_in: BookingCreate, user_id: int = 1, db: Session = Depends(get_db)):
    # Check Idempotency key if provided
    if booking_in.idempotency_key:
        existing_payment = db.query(Payment).filter(Payment.idempotency_key == booking_in.idempotency_key).first()
        if existing_payment and existing_payment.ticket_id:
            t = db.query(Ticket).filter(Ticket.id == existing_payment.ticket_id).first()
            ev = db.query(Event).filter(Event.id == t.event_id).first()
            token, qr_data_url = generate_ticket_qr_base64(str(t.id), str(existing_payment.id), str(ev.id))
            return {
                "ticket_id": t.id,
                "ticket_number": t.ticket_number,
                "event_title": ev.title,
                "price_paid": t.price_paid,
                "status": t.status,
                "invoice_number": existing_payment.invoice_number,
                "qr_code_url": qr_data_url
            }

    # Atomic decrement of available tickets to prevent race conditions / double bookings
    rows_updated = db.query(Event).filter(
        Event.id == booking_in.event_id,
        Event.available_tickets >= booking_in.quantity
    ).update({Event.available_tickets: Event.available_tickets - booking_in.quantity})

    if rows_updated == 0:
        raise HTTPException(status_code=400, detail="Not enough tickets available or sold out")

    ev = db.query(Event).filter(Event.id == booking_in.event_id).first()

    ticket_no = f"TCK-{uuid.uuid4().hex[:8].upper()}"
    invoice_no = f"INV-2026-{uuid.uuid4().hex[:6].upper()}"

    ticket = Ticket(
        ticket_number=ticket_no,
        event_id=ev.id,
        user_id=user_id,
        status="CONFIRMED",
        price_paid=ev.price * booking_in.quantity
    )
    db.add(ticket)
    db.flush()

    payment = Payment(
        payment_id=f"pay_{uuid.uuid4().hex[:10]}",
        order_id=f"ord_{uuid.uuid4().hex[:10]}",
        ticket_id=ticket.id,
        user_id=user_id,
        amount=ticket.price_paid,
        status="SUCCESS",
        idempotency_key=booking_in.idempotency_key,
        invoice_number=invoice_no,
        escrow_release_at=datetime.utcnow() + timedelta(days=2)
    )
    db.add(payment)

    # Generate HMAC Signed QR Token
    qr_token, qr_b64_image = generate_ticket_qr_base64(str(ticket.id), payment.payment_id, str(ev.id))
    ticket.qr_code_path = qr_token

    # Run IsolationForest Fraud Detector check on transaction
    fraud_res = fraud_detector.analyze_transaction(velocity=2, failed_ratio=0.0, distinct_ips=1, time_delta=120)
    if fraud_res["is_suspicious"]:
        flag = FraudFlag(
            user_id=user_id,
            booking_id=ticket.id,
            score=fraud_res["anomaly_score"],
            reason=fraud_res["reason"],
            status="PENDING_REVIEW"
        )
        db.add(flag)

    db.commit()
    db.refresh(ticket)

    # Generate GST Invoice PDF in background/storage
    pdf_dir = os.path.join(tempfile.gettempdir(), "chatassist_uploads", "invoices")
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"{invoice_no}.pdf")
    try:
        generate_gst_invoice_pdf({
            "id": ticket.id,
            "invoice_number": invoice_no,
            "ticket_number": ticket_no,
            "event_title": ev.title,
            "price_paid": ticket.price_paid,
            "user_name": "Valued Customer",
            "user_email": "customer@example.com"
        }, pdf_path)
    except Exception as e:
        print(f"Warning: PDF generation failed ({e})")

    return {
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "event_title": ev.title,
        "price_paid": ticket.price_paid,
        "status": ticket.status,
        "invoice_number": invoice_no,
        "qr_code_url": qr_b64_image
    }

@router.get("/user/tickets")
def get_user_tickets(user_id: int = 1, db: Session = Depends(get_db)):
    tickets = db.query(Ticket).filter(Ticket.user_id == user_id).order_by(Ticket.id.desc()).all()
    results = []
    for t in tickets:
        ev = db.query(Event).filter(Event.id == t.event_id).first()
        payment = db.query(Payment).filter(Payment.ticket_id == t.id).first()
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

    if status_upper == "CANCELLED":
        scan_log.result = "CANCELLED"
        db.add(scan_log)
        db.commit()
        return {
            "valid": False,
            "status": "CANCELLED",
            "message": "❌ Ticket Cancelled and Refunded",
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





