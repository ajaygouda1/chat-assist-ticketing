from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, JSON, Text
from datetime import datetime
from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    actor_role = Column(String, default="SYSTEM")
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=True)
    ip_address = Column(String, nullable=True)
    details = Column(JSON, default=dict)
    timestamp = Column(DateTime, default=datetime.utcnow)


class FraudSignal(Base):
    __tablename__ = "fraud_signals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    risk_score = Column(Float, default=0.0)  # 0 to 100
    reasons = Column(JSON, default=list)  # ["+30 unusual booking velocity", "+20 repeated failed payments"]
    status = Column(String, default="ACTIVE")  # ACTIVE, DISMISSED, RESOLVED
    flagged_at = Column(DateTime, default=datetime.utcnow)
