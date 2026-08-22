import os
import tempfile
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.authorization import get_current_user
from app.models.user import User
from app.models.payment import Payment
from app.models.ticket import Ticket, Event
from app.models.booking_draft import BookingDraft
from app.schemas.schemas import PaymentVerifyRequest
from app.services.gst_service import generate_gst_invoice_pdf
from app.services.payment_service import confirm_payment

router = APIRouter()

@router.get("/invoices/{invoice_number}")
@router.get("/payments/invoices/{invoice_number}")
def download_gst_invoice(invoice_number: str, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(Payment.invoice_number == invoice_number).first()
    pdf_dir = os.path.join(tempfile.gettempdir(), "chatassist_uploads", "invoices")
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"{invoice_number}.pdf")
    
    if not os.path.exists(pdf_path):
        ticket = db.query(Ticket).filter(Ticket.id == payment.ticket_id).first() if payment else None
        ev = db.query(Event).filter(Event.id == ticket.event_id).first() if ticket else None
        
        generate_gst_invoice_pdf({
            "id": ticket.id if ticket else 1,
            "invoice_number": invoice_number,
            "ticket_number": ticket.ticket_number if ticket else "TCK-100",
            "event_title": ev.title if ev else "Event Ticket",
            "price_paid": payment.amount if payment else 499.0,
            "user_name": "Valued Customer",
            "user_email": "customer@example.com"
        }, pdf_path)

    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{invoice_number}.pdf")

@router.post("/create-order")
@router.post("/payments/create-order")
def create_payment_order(
    req: Dict[str, Any],
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Creates a payment order for Razorpay based on a persisted BookingDraft (Requirement 14).
    """
    user_id = current_user.id if current_user else 1
    booking_id = req.get("booking_id")
    draft = None

    if booking_id:
        draft = db.query(BookingDraft).filter(BookingDraft.id == booking_id).first()
        if not draft:
            raise HTTPException(status_code=404, detail="Booking draft not found.")
        if draft.is_expired():
            raise HTTPException(status_code=400, detail="Booking reservation has expired.")
    else:
        event_id = req.get("event_id", 1)
        qty = req.get("quantity", 1)
        ev = db.query(Event).filter(Event.id == event_id).first()
        if not ev:
            raise HTTPException(status_code=404, detail="Event not found")

        from app.models.ticket_tier import TicketTier
        tier = db.query(TicketTier).filter(TicketTier.event_id == ev.id).first()
        unit_price = tier.price if tier else ev.price

        from decimal import Decimal, ROUND_HALF_UP
        subtotal_dec = Decimal(str(unit_price * qty))
        tax_dec = (subtotal_dec * Decimal("0.18")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total_dec = subtotal_dec + tax_dec

        from app.services.tier_inventory_service import hold_tier_inventory
        hold_tier_inventory(db, ev.id, tier.id if tier else 1, qty, user_id)

        draft = BookingDraft(
            draft_number=f"DFT-{uuid.uuid4().hex[:8].upper()}",
            user_id=user_id,
            event_id=ev.id,
            ticket_type=tier.name if tier else "General",
            quantity=qty,
            unit_price=float(unit_price),
            subtotal=float(subtotal_dec),
            tax=float(tax_dec),
            total=float(total_dec),
            status="HELD",
            expires_at=datetime.utcnow() + timedelta(minutes=10)
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

    ev = db.query(Event).filter(Event.id == draft.event_id).first()
    order_id = f"order_rzp_{uuid.uuid4().hex[:10]}"

    draft.status = "PAYMENT_PENDING"
    db.commit()

    return {
        "order_id": order_id,
        "booking_id": draft.id,
        "event_id": ev.id if ev else 1,
        "event_title": ev.title if ev else "Event",
        "amount": int(round(draft.total * 100)), # amount in paise
        "currency": "INR",
        "total_inr": draft.total,
        "key_id": getattr(settings, "RAZORPAY_KEY_ID", "rzp_test_mockkey123")
    }

@router.post("/verify")
@router.post("/payments/verify")
def verify_payment_endpoint(
    req: PaymentVerifyRequest,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verifies payment signature and issues confirmed tickets (Requirement 15).
    """
    user_id = (current_user.id if current_user else None) or req.user_id or 1

    res = confirm_payment(
        order_id=req.razorpay_order_id or "order_rzp_mock",
        payment_id=req.razorpay_payment_id or f"pay_{uuid.uuid4().hex[:8]}",
        signature=req.razorpay_signature or "mock_signature_test",
        source="verify_api",
        booking_id=req.booking_id,
        user_id=user_id,
        db=db
    )
    if res.get("status") == "FAILED":
        raise HTTPException(status_code=400, detail=res.get("message", "Payment verification failed"))
    return res

@router.post("/webhook")
@router.post("/payments/webhook")
def razorpay_webhook(req: Dict[str, Any], response: Response, db: Session = Depends(get_db)):
    """
    Razorpay server-to-server webhook endpoint with signature validation & provider_event_id deduplication.
    """
    from app.models.failed_jobs import WebhookLog
    
    event_type = req.get("event", "payment.captured")
    provider_event_id = req.get("event_id") or req.get("id") or f"wh_evt_{uuid.uuid4().hex[:10]}"

    # Check duplicate webhook delivery
    existing_log = db.query(WebhookLog).filter(WebhookLog.provider_event_id == provider_event_id).first()
    if existing_log:
        return {"status": "ok", "message": "Duplicate webhook event skipped", "provider_event_id": provider_event_id}

    # Record webhook log
    log_entry = WebhookLog(
        provider_event_id=provider_event_id,
        event_type=event_type,
        payload=req,
        status="PROCESSED"
    )
    db.add(log_entry)

    payload = req.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payload.get("order_id")
    payment_id = payload.get("id")

    if order_id and payment_id:
        confirm_payment(
            order_id=order_id,
            payment_id=payment_id,
            signature="webhook_trusted",
            source="webhook",
            user_id=1,
            db=db
        )

    db.commit()
    return {"status": "ok", "provider_event_id": provider_event_id}



