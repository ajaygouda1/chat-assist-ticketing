from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.openai_service import ai_service
from app.models.customer import ChatMessage

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_copilot(req: ChatRequest, user_id: int = 1, db: Session = Depends(get_db)):
    res = ai_service.process_chat_message(req.message, user_id=user_id, db=db)
    
    # Save message in chat history DB
    msg_user = ChatMessage(user_id=user_id, sender="user", message=req.message)
    msg_bot = ChatMessage(
        user_id=user_id,
        sender="assistant",
        message=res["reply"],
        intent_detected=res["intent"],
        confidence=str(res["confidence"]),
        is_grounded="TRUE" if res["grounding_status"] == "GROUNDED_LIVE_DB" else "FALSE"
    )
    db.add(msg_user)
    db.add(msg_bot)
    db.commit()

    return res
