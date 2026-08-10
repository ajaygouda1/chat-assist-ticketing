from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.ticket import Event, Ticket
from app.schemas.schemas import EventResponse
from app.ml.recommender import recommender

router = APIRouter()

@router.get("/recommendations", response_model=List[EventResponse])
def get_recommendations(user_id: int = 1, db: Session = Depends(get_db)):
    user_tickets = db.query(Ticket).filter(Ticket.user_id == user_id).all()
    attended_event_ids = [t.event_id for t in user_tickets]
    
    all_events = db.query(Event).all()
    recs = recommender.recommend(attended_event_ids, all_events, top_k=4)
    return recs
