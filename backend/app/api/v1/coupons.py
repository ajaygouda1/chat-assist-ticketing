from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_db
from app.models.ml_models import Coupon

router = APIRouter()

class CouponValidationRequest(BaseModel):
    code: str
    total_amount: float

@router.post("/coupons/validate")
def validate_coupon(req: CouponValidationRequest, db: Session = Depends(get_db)):
    code_clean = req.code.strip().upper()
    coupon = db.query(Coupon).filter(Coupon.code == code_clean, Coupon.is_active == True).first()
    
    if not coupon:
        raise HTTPException(status_code=404, detail="Invalid promo coupon code")

    if coupon.used_count >= coupon.max_uses:
        raise HTTPException(status_code=400, detail="Coupon usage limit reached")

    discount = 0.0
    if coupon.discount_type == "PERCENTAGE":
        discount = round((req.total_amount * coupon.discount_value) / 100.0, 2)
    else:
        discount = min(coupon.discount_value, req.total_amount)

    final_price = max(0.0, req.total_amount - discount)

    return {
        "valid": True,
        "code": coupon.code,
        "discount_type": coupon.discount_type,
        "discount_value": coupon.discount_value,
        "discount_amount": discount,
        "final_price": final_price
    }
