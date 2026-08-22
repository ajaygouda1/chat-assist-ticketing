import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.authorization import get_current_user, require_roles
from app.models.user import User
from app.models.support_announcement import SupportTicket, SupportTicketMessage, Announcement
from app.schemas.schemas import SupportTicketCreateRequest, SupportMessageRequest, AnnouncementCreateRequest
from app.models.ticket import Ticket, Event

router = APIRouter()

@router.post("/support/tickets")
def create_support_ticket(req: SupportTicketCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tkt_num = f"SUP-{uuid.uuid4().hex[:6].upper()}"
    ticket = SupportTicket(
        ticket_number=tkt_num,
        user_id=current_user.id,
        category=req.category,
        subject=req.subject,
        description=req.description,
        event_id=req.event_id,
        booking_ticket_id=req.booking_ticket_id,
        status="OPEN"
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket

@router.get("/support/tickets/my")
def list_my_support_tickets(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    tickets = db.query(SupportTicket).filter(SupportTicket.user_id == current_user.id).order_by(SupportTicket.created_at.desc()).all()
    return tickets

@router.get("/admin/support/tickets")
def list_all_support_tickets(current_user: User = Depends(require_roles(["admin", "organizer"])), db: Session = Depends(get_db)):
    tickets = db.query(SupportTicket).order_by(SupportTicket.created_at.desc()).all()
    return tickets

@router.post("/support/tickets/{ticket_id}/reply")
def reply_to_ticket(ticket_id: int, req: SupportMessageRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Support ticket not found")

    msg = SupportTicketMessage(
        ticket_id=ticket.id,
        sender_id=current_user.id,
        sender_role=current_user.role,
        message=req.message
    )
    db.add(msg)
    if current_user.role in ["admin", "super_admin"]:
        ticket.status = "WAITING_FOR_USER"
    else:
        ticket.status = "IN_PROGRESS"
    db.commit()
    return {"status": "reply_added"}

@router.post("/organizer/events/{event_id}/announcements")
def post_organizer_announcement(event_id: int, req: AnnouncementCreateRequest, current_user: User = Depends(require_roles(["organizer", "admin"])), db: Session = Depends(get_db)):
    tickets_count = db.query(Ticket).filter(Ticket.event_id == event_id, Ticket.status == "CONFIRMED").count()
    anc = Announcement(
        event_id=event_id,
        organizer_id=current_user.id,
        title=req.title,
        message=req.message,
        recipient_count=tickets_count
    )
    db.add(anc)
    db.commit()
    db.refresh(anc)
    return {"message": f"Announcement broadcasted to {tickets_count} confirmed attendees", "announcement": anc}
