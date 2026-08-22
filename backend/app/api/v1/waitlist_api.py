from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.authorization import get_current_user
from app.models.user import User
from app.schemas.schemas import WaitlistCreateRequest
from app.services.waitlist_service import join_waitlist
from app.models.waitlist import WaitlistEntry

router = APIRouter()

@router.post("/events/{event_id}/waitlist")
def add_to_waitlist(event_id: int, req: WaitlistCreateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    entry = join_waitlist(db, event_id, current_user.id, req.ticket_tier, req.requested_quantity)
    return {
        "message": "Added to event waitlist",
        "waitlist_id": entry.id,
        "position": entry.position,
        "status": entry.status
    }

@router.get("/events/{event_id}/waitlist/status")
def get_waitlist_status(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    entry = db.query(WaitlistEntry).filter(
        WaitlistEntry.event_id == event_id,
        WaitlistEntry.user_id == current_user.id
    ).first()
    if not entry:
        return {"on_waitlist": False}
    return {
        "on_waitlist": True,
        "position": entry.position,
        "status": entry.status,
        "purchase_deadline": entry.purchase_deadline.isoformat() if entry.purchase_deadline else None
    }
