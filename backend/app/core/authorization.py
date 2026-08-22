import os
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
    Extracts current authenticated user strictly from JWT Bearer token.
    Dev bypass fallback is permitted ONLY if ENV != production AND ALLOW_DEV_AUTH_BYPASS=true.
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

    # Optional development-only bypass (strictly disabled in production)
    dev_bypass_enabled = (settings.ENV != "production") and (os.getenv("ALLOW_DEV_AUTH_BYPASS", "false").lower() == "true")
    if dev_bypass_enabled:
        uid = x_user_id or 1
        user = db.query(User).filter(User.id == uid).first()
        if user:
            return user

    return None

def require_current_user(
    current_user: Optional[User] = Depends(get_current_user)
) -> User:
    """
    Ensures that a request has a valid authenticated user.
    Raises 401 Unauthorized if missing.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please include a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    return current_user

def require_event_owner(
    event_id: int,
    current_user: User = Depends(require_current_user),
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

    user_role = (current_user.role or "customer").lower()
    if user_role in ["super_admin", "admin"]:
        return event

    if event.organizer_id is not None and event.organizer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Forbidden: You can only edit or modify your own events (Event owned by organizer #{event.organizer_id})"
        )

    return event

def require_roles(allowed_roles: list):
    """
    Dependency factory to check if the authenticated user has one of the allowed roles.
    Super admin is always allowed.
    """
    def role_checker(current_user: User = Depends(require_current_user)):
        user_role = (current_user.role or "customer").lower()
        allowed = [r.lower() for r in allowed_roles] + ["super_admin"]
        
        if user_role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden: Action requires one of roles {allowed_roles}, but user has role '{user_role}'"
            )
        return current_user
    return role_checker
