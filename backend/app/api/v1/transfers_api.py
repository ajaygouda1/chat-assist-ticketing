from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.authorization import get_current_user
from app.models.user import User
from app.schemas.schemas import TransferInitiateRequest
from app.services.transfer_service import initiate_ticket_transfer, accept_ticket_transfer
from app.models.ticket_transfer import TicketTransfer

router = APIRouter()

@router.post("/tickets/{ticket_id}/transfer")
def transfer_ticket(ticket_id: int, req: TransferInitiateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    transfer = initiate_ticket_transfer(db, ticket_id, current_user.id, req.recipient_email)
    return {
        "message": f"Transfer request initiated to {req.recipient_email}",
        "transfer_id": transfer.id,
        "status": transfer.status
    }

@router.post("/transfers/{transfer_id}/accept")
def accept_transfer(transfer_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    new_ticket = accept_ticket_transfer(db, transfer_id, current_user.id)
    return {
        "message": "Ticket transfer accepted successfully!",
        "new_ticket_id": new_ticket.id,
        "new_ticket_number": new_ticket.ticket_number
    }

@router.get("/tickets/transfers/history")
def transfer_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    sent = db.query(TicketTransfer).filter(TicketTransfer.from_user_id == current_user.id).all()
    received = db.query(TicketTransfer).filter(TicketTransfer.to_user_email == current_user.email).all()
    return {"sent_transfers": sent, "received_transfers": received}
