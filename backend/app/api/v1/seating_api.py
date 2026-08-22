from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.authorization import get_current_user
from app.models.user import User
from app.schemas.schemas import HoldSeatsRequest
from app.services.seating_service import get_event_seat_map, hold_seats_atomic

router = APIRouter()

@router.get("/events/{event_id}/seatmap")
def get_seatmap(event_id: int, db: Session = Depends(get_db)):
    return get_event_seat_map(db, event_id)

@router.post("/events/{event_id}/hold-seats")
def hold_seats(event_id: int, req: HoldSeatsRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    seats = hold_seats_atomic(db, event_id, current_user.id, req.seat_codes)
    return {
        "message": f"Successfully held {len(seats)} seats for 10 minutes",
        "held_seats": [s.seat_code for s in seats],
        "held_until": seats[0].held_until.isoformat() if seats else None
    }
