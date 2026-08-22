from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.authorization import get_current_user
from app.models.user import User
from app.models.notification import Notification, SavedEvent, UserFollowOrganizer

router = APIRouter()

@router.get("/notifications")
def get_user_notifications(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifs = db.query(Notification).filter(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).all()
    unread_count = db.query(Notification).filter(Notification.user_id == current_user.id, Notification.is_read == False).count()
    return {"notifications": notifs, "unread_count": unread_count}

@router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notif = db.query(Notification).filter(Notification.id == notification_id, Notification.user_id == current_user.id).first()
    if notif:
        notif.is_read = True
        db.commit()
    return {"status": "success"}

@router.post("/events/{event_id}/save")
def toggle_save_event(event_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    existing = db.query(SavedEvent).filter(SavedEvent.event_id == event_id, SavedEvent.user_id == current_user.id).first()
    if existing:
        db.delete(existing)
        db.commit()
        return {"saved": False, "message": "Event removed from saved events"}
    else:
        saved = SavedEvent(user_id=current_user.id, event_id=event_id)
        db.add(saved)
        db.commit()
        return {"saved": True, "message": "Event saved successfully"}

@router.get("/events/saved/my")
def get_saved_events(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    saved = db.query(SavedEvent).filter(SavedEvent.user_id == current_user.id).all()
    return [s.event_id for s in saved]
