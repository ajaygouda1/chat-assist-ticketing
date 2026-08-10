from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.ticket import Event
from app.schemas.schemas import EventResponse
from app.ml.semantic_search import semantic_search

router = APIRouter()

@router.get("/search/semantic", response_model=List[EventResponse])
def search_semantic(q: str = Query(..., description="Fuzzy search query"), db: Session = Depends(get_db)):
    all_events = db.query(Event).all()
    matches = semantic_search.search(q, all_events, top_k=6)
    return matches
