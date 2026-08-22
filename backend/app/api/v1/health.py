import time
import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db, engine
from app.core.config import settings
from app.core.redis import redis_manager

router = APIRouter()

@router.get("/health")
@router.get("/health/status")
def get_system_health(db: Session = Depends(get_db)):
    start = time.time()
    dialect_name = engine.dialect.name.lower()

    # 1. Real DB Ping
    db_status = "healthy"
    if settings.ENV == "production" and dialect_name == "sqlite":
        db_status = "misconfigured"
    else:
        try:
            db.execute(text("SELECT 1"))
        except Exception as e:
            db_status = "unhealthy"

    # 2. Redis Ping Check
    redis_status = "healthy" if not redis_manager.using_fallback else "fallback"

    # 3. Payment Provider Configured Check
    payment_configured = bool(
        settings.RAZORPAY_KEY_ID and 
        settings.RAZORPAY_KEY_SECRET and 
        settings.RAZORPAY_KEY_ID != "rzp_test_mockkey123"
    ) or (settings.PAYMENT_MODE == "mock" and settings.ENV != "production")

    latency_ms = round((time.time() - start) * 1000, 2)
    overall_status = "healthy" if (db_status == "healthy" and redis_status in ["healthy", "fallback"]) else "degraded"

    return {
        "status": overall_status,
        "environment": settings.ENV,
        "database": {
            "status": db_status,
            "dialect": dialect_name
        },
        "redis": {
            "status": redis_status
        },
        "payment": {
            "configured": payment_configured
        },
        "metrics": {
            "latency_ms": latency_ms
        }
    }
