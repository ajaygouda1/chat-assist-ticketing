from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from datetime import datetime
from app.core.database import Base

class FailedJob(Base):
    __tablename__ = "failed_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=True)
    attempts = Column(Integer, default=1)
    last_error = Column(Text, nullable=True)
    next_retry_at = Column(DateTime, nullable=True)
    status = Column(String, default="FAILED")  # FAILED, RETRYSCHEDULED, RESOLVED
    created_at = Column(DateTime, default=datetime.utcnow)


class WebhookLog(Base):
    __tablename__ = "webhook_logs"

    id = Column(Integer, primary_key=True, index=True)
    provider_event_id = Column(String, unique=True, index=True, nullable=False)
    event_type = Column(String, nullable=False)
    payload = Column(JSON, default=dict)
    status = Column(String, default="PROCESSED")  # PROCESSED, DUPLICATE_SKIPPED, FAILED
    processed_at = Column(DateTime, default=datetime.utcnow)
