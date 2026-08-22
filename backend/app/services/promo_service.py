from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any
from fastapi import HTTPException
from app.models.promo import PromoCode, PromoRedemption

def validate_and_apply_promo(db: Session, code: str, user_id: int, event_id: int, subtotal: float) -> Dict[str, Any]:
    """
    Validates promo code and computes backend discount.
    """
    promo = db.query(PromoCode).filter(PromoCode.code == code.upper(), PromoCode.is_active == True).first()
    if not promo:
        raise HTTPException(status_code=400, detail="Invalid or expired promo code")

    now = datetime.utcnow()
    if promo.expiry_date and promo.expiry_date < now:
        raise HTTPException(status_code=400, detail="Promo code has expired")

    if promo.used_count >= promo.max_uses:
        raise HTTPException(status_code=400, detail="Promo code usage limit reached")

    if subtotal < promo.min_order_amount:
        raise HTTPException(status_code=400, detail=f"Minimum order amount of ₹{promo.min_order_amount} required for this promo")

    # Check per user limit
    user_redemptions = db.query(PromoRedemption).filter(
        PromoRedemption.promo_id == promo.id,
        PromoRedemption.user_id == user_id
    ).count()

    if user_redemptions >= promo.per_user_limit:
        raise HTTPException(status_code=400, detail="You have already reached the maximum usage limit for this promo code")

    # Check applicable events
    if promo.applicable_event_ids and len(promo.applicable_event_ids) > 0:
        if event_id not in promo.applicable_event_ids:
            raise HTTPException(status_code=400, detail="Promo code is not applicable for this event")

    # Compute discount
    if promo.discount_type == "PERCENTAGE":
        discount = subtotal * (promo.discount_value / 100.0)
        if promo.max_discount_amount and discount > promo.max_discount_amount:
            discount = promo.max_discount_amount
    else:  # FIXED / FLAT
        discount = promo.discount_value

    discount = min(discount, subtotal)
    discount = round(discount, 2)
    final_total = round(subtotal - discount, 2)

    return {
        "promo_id": promo.id,
        "code": promo.code,
        "discount_type": promo.discount_type,
        "discount_value": promo.discount_value,
        "discount_amount": discount,
        "subtotal": subtotal,
        "final_total": final_total
    }
