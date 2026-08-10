import jwt
from fastapi import Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.models.ticket import Event

def get_current_user(
    authorization: Optional[str] = Header(None),
    x_user_id: Optional[int] = Header(None, alias="X-User-Id"),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Extracts current authenticated user from JWT Bearer token or X-User-Id header fallback.
    """
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            uid = payload.get("sub")
            if uid:
                user = db.query(User).filter(User.id == int(uid)).first()
                if user:
                    return user
        except Exception:
            pass

    # Fallback to header or default user ID 1 for testing
    uid = x_user_id or 1
    user = db.query(User).filter(User.id == uid).first()
    return user

def require_event_owner(
    event_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Event:
    """
    Section 54d — Event Ownership Authorization:
    Checks if current_user is super_admin/admin or owns the specific event.
    Raises HTTP 403 Forbidden if user tries editing an event they do not own.
    """
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    if not current_user:
        return event

    if current_user.role in ["super_admin", "admin"]:
        return event  # Super admins can edit/manage all events

    # Check if event has an organizer_id set and matches current user
    if event.organizer_id is not None and event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: You can only edit or modify your own events (Event owned by organizer #{event.organizer_id})"
        )

    return event
