from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.models.ml_models import FraudFlag
from app.schemas.schemas import FraudFlagResponse

router = APIRouter()

@router.get("/admin/fraud-flags", response_model=List[FraudFlagResponse])
def get_fraud_flags(db: Session = Depends(get_db)):
    flags = db.query(FraudFlag).all()
    if not flags:
        # Seed mock flag for demonstration
        f1 = FraudFlag(user_id=4, booking_id=102, score=0.88, reason="Rapid 5x bookings in 30 seconds across 3 IPs", status="PENDING_REVIEW")
        db.add(f1)
        db.commit()
        flags = [f1]
    return flags

@router.post("/admin/fraud-flags/{flag_id}/review")
def review_fraud_flag(flag_id: int, action: str, db: Session = Depends(get_db)):
    flag = db.query(FraudFlag).filter(FraudFlag.id == flag_id).first()
    if not flag:
        raise HTTPException(status_code=404, detail="Fraud flag not found")
    
    if action in ["CLEARED", "CONFIRMED"]:
        flag.status = action
        db.commit()
    return {"status": "success", "flag_id": flag_id, "new_status": flag.status}
