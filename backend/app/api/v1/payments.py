import os
import tempfile
import uuid
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.payment import Payment
from app.models.ticket import Ticket, Event
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
def create_payment_order(req: Dict[str, Any], user_id: int = 1, db: Session = Depends(get_db)):
    """
    Creates a payment order for Razorpay or simulation (§8 & §49c).
    """
    event_id = req.get("event_id", 1)
    quantity = req.get("quantity", 1)
    ev = db.query(Event).filter(Event.id == event_id).first()
    if not ev:
        raise HTTPException(status_code=404, detail="Event not found")

    unit_price = ev.price
    if req.get("ticket_type", "").lower().startswith("vip"):
        unit_price = round(ev.price * 1.5, 0)

    subtotal = unit_price * quantity
    tax = round(subtotal * 0.18, 2)
    total = subtotal + tax

    order_id = f"order_rzp_{uuid.uuid4().hex[:10]}"
    booking_id = int(uuid.uuid4().int % 1000000)

    return {
        "order_id": order_id,
        "booking_id": booking_id,
        "event_id": ev.id,
        "event_title": ev.title,
        "amount": int(total * 100), # amount in paise
        "currency": "INR",
        "total_inr": total,
        "key_id": os.getenv("RAZORPAY_KEY_ID", "rzp_test_mockkey123")
    }

@router.post("/verify")
@router.post("/payments/verify")
def verify_payment_endpoint(req: PaymentVerifyRequest, db: Session = Depends(get_db)):
    """
    Verifies payment signature and issues confirmed ticket (§49e).
    """
    res = confirm_payment(
        order_id=req.razorpay_order_id or "order_rzp_mock",
        payment_id=req.razorpay_payment_id or f"pay_{uuid.uuid4().hex[:8]}",
        signature=req.razorpay_signature or "mock_signature_test",
        source="verify_api",
        booking_id=req.booking_id,
        user_id=req.user_id or 1,
        db=db
    )
    if res.get("status") == "FAILED":
        raise HTTPException(status_code=400, detail=res.get("message", "Payment verification failed"))
    return res

@router.post("/webhook")
@router.post("/payments/webhook")
def razorpay_webhook(req: Dict[str, Any], db: Session = Depends(get_db)):
    """
    Razorpay server-to-server webhook endpoint (§49e).
    Idempotently handles payment.captured events.
    """
    event_type = req.get("event")
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
    return {"status": "ok"}


