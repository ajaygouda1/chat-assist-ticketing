import uuid
import tempfile
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.ticket import Event, Ticket
from app.models.payment import Payment
from app.models.booking_draft import BookingDraft
from app.services.qr_service import generate_ticket_qr_base64
from app.services.gst_service import generate_gst_invoice_pdf
from app.services.tier_inventory_service import confirm_tier_inventory_payment

def verify_razorpay_signature(order_id: str, payment_id: str, signature: str) -> bool:
    mode = os.getenv("PAYMENT_MODE", "mock").lower()
    env = os.getenv("ENV", "development").lower()

    # Mock signature acceptance strictly restricted to non-production environments when PAYMENT_MODE=mock
    if mode == "mock" and env != "production":
        return True

    secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    if not secret or not signature or signature == "mock_signature_test":
        return False

    import hmac, hashlib
    expected_sig = hmac.new(
        secret.encode(),
        f"{order_id}|{payment_id}".encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected_sig, signature)

def confirm_payment(
    order_id: str,
    payment_id: str,
    signature: str,
    source: str = "verify_api",
    booking_id: Optional[int] = None,
    user_id: int = 1,
    db: Session = None
) -> Dict[str, Any]:
    """
    Idempotent, transactional payment confirmation service.
    Converts held inventory to sold, creates individual admission Ticket rows with HMAC signed QR codes.
    """
    if not verify_razorpay_signature(order_id, payment_id, signature):
        return {"status": "FAILED", "message": "Invalid payment signature verification."}

    # 1. Check existing confirmed payment by order_id or payment_id (Idempotency)
    existing_payment = db.query(Payment).filter(
        (Payment.order_id == order_id) | (Payment.payment_id == payment_id)
    ).first()

    if existing_payment:
        existing_tickets = db.query(Ticket).filter(
            Ticket.user_id == existing_payment.user_id
        ).order_by(Ticket.id.asc()).all()

        ev = None
        if existing_tickets:
            ev = db.query(Event).filter(Event.id == existing_tickets[0].event_id).first()

        ticket_list = []
        for t in existing_tickets:
            token, qr_url = generate_ticket_qr_base64(str(t.id), existing_payment.payment_id, str(ev.id if ev else 1))
            ticket_list.append({
                "id": t.id,
                "ticket_number": t.ticket_number,
                "event_title": ev.title if ev else "Event",
                "price_paid": t.price_paid,
                "status": t.status,
                "qr_code_url": qr_url,
                "qr_token": token
            })

        first_t = ticket_list[0] if ticket_list else {}
        if existing_payment.ticket_id:
            matching = [t for t in ticket_list if t["id"] == existing_payment.ticket_id]
            if matching:
                first_t = matching[0]

        return {
            "status": "ALREADY_CONFIRMED",
            "message": "Payment was already confirmed.",
            "ticket": first_t,
            "tickets": ticket_list,
            "invoice_number": existing_payment.invoice_number
        }

    draft = None
    if booking_id:
        draft = db.query(BookingDraft).filter(BookingDraft.id == booking_id).first()

    # Retrieve event and quantity from draft
    if draft:
        event_id = draft.event_id
        qty = draft.quantity
        unit_price = draft.unit_price
        user_id = draft.user_id
        ticket_type = draft.ticket_type
    else:
        ev = db.query(Event).filter(Event.available_tickets > 0).first()
        if not ev:
            return {"status": "FAILED", "message": "No available event found for booking."}
        event_id = ev.id
        qty = 1
        unit_price = ev.price
        ticket_type = "General"

    ev = db.query(Event).filter(Event.id == event_id).first()
    if not ev:
        return {"status": "FAILED", "message": "Event not found."}

    # Convert tier held inventory -> sold quantity
    confirm_tier_inventory_payment(db, ev.id, ticket_type, qty)

    invoice_no = f"INV-2026-{uuid.uuid4().hex[:6].upper()}"
    actual_payment_id = payment_id or f"pay_{uuid.uuid4().hex[:10]}"
    actual_order_id = order_id or f"ord_{uuid.uuid4().hex[:10]}"

    total_amount = draft.total if draft else (unit_price * qty * 1.18)

    # Primary Payment Record
    payment = Payment(
        payment_id=actual_payment_id,
        order_id=actual_order_id,
        user_id=user_id,
        amount=total_amount,
        status="SUCCESS",
        invoice_number=invoice_no,
        escrow_release_at=datetime.utcnow() + timedelta(days=2)
    )
    db.add(payment)
    db.flush()

    # Create 1 Ticket row per admission (Requirement 19)
    per_ticket_price = round(total_amount / qty, 2)
    created_tickets = []

    for i in range(qty):
        t_no = f"TCK-{uuid.uuid4().hex[:8].upper()}"
        t = Ticket(
            ticket_number=t_no,
            event_id=ev.id,
            user_id=user_id,
            status="CONFIRMED",
            price_paid=per_ticket_price
        )
        db.add(t)
        db.flush()

        qr_token, qr_b64 = generate_ticket_qr_base64(str(t.id), payment.payment_id, str(ev.id))
        t.qr_code_path = qr_token

        created_tickets.append({
            "id": t.id,
            "ticket_number": t.ticket_number,
            "event_title": ev.title,
            "price_paid": t.price_paid,
            "status": t.status,
            "invoice_number": invoice_no,
            "qr_code_url": qr_b64,
            "qr_token": qr_token,
            "date_str": ev.date_str,
            "location": ev.location
        })

    if created_tickets:
        payment.ticket_id = created_tickets[0]["id"]

    if draft:
        draft.status = "CONFIRMED"

    db.commit()

    # Generate GST Invoice PDF
    pdf_dir = os.path.join(tempfile.gettempdir(), "chatassist_uploads", "invoices")
    os.makedirs(pdf_dir, exist_ok=True)
    pdf_path = os.path.join(pdf_dir, f"{invoice_no}.pdf")
    try:
        generate_gst_invoice_pdf({
            "id": created_tickets[0]["id"] if created_tickets else 1,
            "invoice_number": invoice_no,
            "ticket_number": created_tickets[0]["ticket_number"] if created_tickets else "TCK-100",
            "event_title": ev.title,
            "price_paid": total_amount,
            "user_name": "Valued Customer",
            "user_email": "customer@example.com"
        }, pdf_path)
    except Exception as e:
        print(f"GST PDF generation notice: {e}")

    return {
        "status": "CONFIRMED",
        "message": f"Payment verified and {qty} ticket(s) issued successfully!",
        "source": source,
        "ticket": created_tickets[0] if created_tickets else {},
        "tickets": created_tickets,
        "invoice_number": invoice_no
    }
