from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from datetime import datetime
from app.core.database import Base

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sender = Column(String, nullable=False)  # user, assistant, system
    message = Column(Text, nullable=False)
    intent_detected = Column(String, nullable=True)
    confidence = Column(String, nullable=True)
    is_grounded = Column(String, default="TRUE")
    language = Column(String, default="en")
    created_at = Column(DateTime, default=datetime.utcnow)
