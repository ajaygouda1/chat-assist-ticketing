import uuid
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi import HTTPException
from app.models.ticket import Ticket, Event
from app.models.user import User
from app.models.ticket_transfer import TicketTransfer
from app.services.qr_service import generate_ticket_qr_base64

def initiate_ticket_transfer(db: Session, ticket_id: int, from_user_id: int, recipient_email: str) -> TicketTransfer:
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id, Ticket.user_id == from_user_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or not owned by user")

    if ticket.status != "CONFIRMED":
        raise HTTPException(status_code=400, detail=f"Cannot transfer ticket with status '{ticket.status}'")

    recipient_user = db.query(User).filter(User.email == recipient_email.lower().strip()).first()
    
    transfer = TicketTransfer(
        ticket_id=ticket.id,
        from_user_id=from_user_id,
        to_user_email=recipient_email.lower().strip(),
        to_user_id=recipient_user.id if recipient_user else None,
        status="PENDING",
        old_ticket_number=ticket.ticket_number
    )
    db.add(transfer)
    db.commit()
    db.refresh(transfer)

    # Auto-accept if recipient already exists in platform
    if recipient_user:
        accept_ticket_transfer(db, transfer.id, recipient_user.id)
    return transfer

def accept_ticket_transfer(db: Session, transfer_id: int, recipient_user_id: int) -> Ticket:
    transfer = db.query(TicketTransfer).filter(TicketTransfer.id == transfer_id).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transfer request not found")

    if transfer.status != "PENDING":
        raise HTTPException(status_code=400, detail=f"Transfer is already '{transfer.status}'")

    old_ticket = db.query(Ticket).filter(Ticket.id == transfer.ticket_id).first()
    if not old_ticket:
        raise HTTPException(status_code=404, detail="Original ticket not found")

    # Invalidate old ticket immediately
    old_ticket.status = "TRANSFERRED"

    # Generate new ticket number & HMAC QR code for recipient
    new_ticket_num = f"TKT-TR-{uuid.uuid4().hex[:8].upper()}"
    new_ticket = Ticket(
        ticket_number=new_ticket_num,
        event_id=old_ticket.event_id,
        user_id=recipient_user_id,
        status="CONFIRMED",
        price_paid=old_ticket.price_paid
    )
    db.add(new_ticket)
    db.flush()

    # Generate HMAC QR code for new ticket
    token, qr_url = generate_ticket_qr_base64(str(new_ticket.id), new_ticket_num, str(old_ticket.event_id))
    new_ticket.qr_code_path = qr_url

    transfer.status = "ACCEPTED"
    transfer.to_user_id = recipient_user_id
    transfer.new_ticket_number = new_ticket_num
    transfer.transferred_at = datetime.utcnow()

    db.commit()
    db.refresh(new_ticket)
    return new_ticket
