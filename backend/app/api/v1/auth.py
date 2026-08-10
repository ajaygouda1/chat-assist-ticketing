import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token
from app.models.user import User
from app.schemas.schemas import UserCreate, UserResponse, Token, LoginRequest

from app.core.authorization import get_current_user

router = APIRouter()

@router.post("/register", response_model=Token)
@router.post("/auth/register", response_model=Token)
def register(user_in: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    referral_code = f"REF-{uuid.uuid4().hex[:6].upper()}"
    hashed_pwd = get_password_hash(user_in.password)
    user = User(
        email=user_in.email,
        name=user_in.name,
        hashed_password=hashed_pwd,
        role=user_in.role or "customer",
        phone=user_in.phone,
        referral_code=referral_code
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    return {"access_token": token, "token_type": "bearer", "user": user}

@router.post("/login", response_model=Token)
@router.post("/auth/login", response_model=Token)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == creds.email).first()
    if not user or not verify_password(creds.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id), "role": user.role, "email": user.email})
    return {"access_token": token, "token_type": "bearer", "user": user}

@router.get("/me", response_model=UserResponse)
@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

