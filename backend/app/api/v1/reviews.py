from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List

from app.core.database import get_db
from app.models.ml_models import Review
from app.models.ticket import Ticket

router = APIRouter()

class ReviewCreate(BaseModel):
    event_id: int
    rating: int
    comment: str

@router.get("/events/{event_id}/reviews")
def get_event_reviews(event_id: int, db: Session = Depends(get_db)):
    reviews = db.query(Review).filter(Review.event_id == event_id).all()
    avg_rating = round(sum(r.rating for r in reviews) / len(reviews), 1) if reviews else 5.0
    return {
        "event_id": event_id,
        "average_rating": avg_rating,
        "total_reviews": len(reviews),
        "reviews": reviews
    }

@router.post("/reviews")
def submit_review(req: ReviewCreate, user_id: int = 1, db: Session = Depends(get_db)):
    # Verify ticket ownership (only valid ticket holders can review)
    ticket = db.query(Ticket).filter(Ticket.event_id == req.event_id, Ticket.user_id == user_id).first()
    if not ticket:
        raise HTTPException(status_code=403, detail="Only verified attendees with a ticket can submit reviews")

    rev = Review(
        user_id=user_id,
        event_id=req.event_id,
        rating=req.rating,
        comment=req.comment,
        user_name="Ajay Kumar"
    )
    db.add(rev)
    db.commit()
    db.refresh(rev)
    return rev
