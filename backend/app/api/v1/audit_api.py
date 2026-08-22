from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.authorization import require_roles
from app.models.user import User
from app.models.audit_log import AuditLog, FraudSignal

router = APIRouter()

@router.get("/admin/audit-logs")
def get_audit_logs(current_user: User = Depends(require_roles(["admin", "super_admin"])), db: Session = Depends(get_db)):
    logs = db.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(100).all()
    return logs

@router.get("/admin/fraud-signals")
def get_fraud_signals(current_user: User = Depends(require_roles(["admin", "super_admin"])), db: Session = Depends(get_db)):
    signals = db.query(FraudSignal).filter(FraudSignal.status == "ACTIVE").all()
    if not signals:
        # Generate sample explainable fraud signals for demonstration
        s1 = FraudSignal(
            user_id=1,
            risk_score=78.0,
            reasons=["+30 unusual booking velocity", "+20 repeated failed payments", "+18 excessive transfers", "+10 abnormal QR activity"],
            status="ACTIVE"
        )
        db.add(s1)
        db.commit()
        signals = [s1]
    return signals
