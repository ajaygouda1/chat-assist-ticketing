from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional

from app.core.database import get_db
from app.schemas.schemas import ChatRequest, ChatResponse
from app.services.openai_service import ai_service
from app.models.customer import ChatMessage
from app.models.conversation import Conversation, ConversationMessage
from app.ai.agent import chat_agent

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_copilot(req: ChatRequest, user_id: int = 1, db: Session = Depends(get_db)):
    active_user_id = req.user_id or user_id or 1

    # Get or create conversation session
    conv = None
    if req.conversation_id:
        conv = db.query(Conversation).filter(Conversation.id == req.conversation_id, Conversation.user_id == active_user_id).first()
    
    if not conv:
        title_snippet = (req.message or "System Event")[:28]
        conv = Conversation(user_id=active_user_id, title=title_snippet or "New Chat")
        db.add(conv)
        db.commit()
        db.refresh(conv)

    # Process system payment verification event via deterministic handler
    if req.event_type == "system_event" or (req.payload and req.payload.get("event") == "PAYMENT_VERIFIED"):
        res = ai_service.process_chat_message(
            message=req.message or "",
            user_id=active_user_id,
            db=db,
            event_type=req.event_type or "system_event",
            payload=req.payload,
            conversation_id=conv.id
        )
        res["conversation_id"] = conv.id
    else:
        # Primary AI-First Agent Processing
        agent_resp = chat_agent.process_message(
            user_message=req.message or "",
            user_id=active_user_id,
            conversation_id=conv.id,
            db=db,
            user_role="customer",
            event_type=req.event_type or "user_message",
            payload=req.payload
        )

        res = {
            "reply": agent_resp.reply,
            "message": agent_resp.message,
            "message_id": agent_resp.message_id,
            "intent": agent_resp.intent or "ai_agent",
            "confidence": 0.99,
            "routed_to": "AI_AGENT",
            "grounding_status": agent_resp.grounding_status,
            "type": agent_resp.type,
            "payload": agent_resp.payload,
            "quick_replies": agent_resp.quick_replies,
            "conversation_id": conv.id,
            "ui": [u.model_dump() for u in agent_resp.ui],
            "state": agent_resp.state
        }

    # Update conversation title if default title
    if conv.title in ["New Chat", "New Conversation"] and req.message:
        conv.title = req.message[:28] + ("..." if len(req.message) > 28 else "")

    # Save messages into conversation history DB
    if req.event_type != "system_event" and req.message:
        msg_user = ConversationMessage(
            conversation_id=conv.id,
            user_id=active_user_id,
            sender="user",
            message=req.message,
            message_type="text"
        )
        db.add(msg_user)

    msg_bot = ConversationMessage(
        conversation_id=conv.id,
        user_id=active_user_id,
        sender="assistant",
        message=res["reply"],
        message_type=res.get("type", "text"),
        intent=res.get("intent"),
        metadata_json={
            "confidence": res.get("confidence"),
            "routed_to": res.get("routed_to"),
            "grounding_status": res.get("grounding_status"),
            "payload": res.get("payload"),
            "quick_replies": res.get("quick_replies"),
            "ui": res.get("ui"),
            "state": res.get("state")
        }
    )
    db.add(msg_bot)

    if req.event_type != "system_event" and req.message:
        legacy_user = ChatMessage(user_id=active_user_id, sender="user", message=req.message)
        db.add(legacy_user)
        
    legacy_bot = ChatMessage(
        user_id=active_user_id,
        sender="assistant",
        message=res["reply"],
        intent_detected=res.get("intent"),
        confidence=str(res.get("confidence")),
        is_grounded="TRUE" if res.get("grounding_status") == "GROUNDED_LIVE_DB" else "FALSE"
    )
    db.add(legacy_bot)

    db.commit()

    return res

@router.get("/chat/conversations")
def get_user_conversations(user_id: int = 1, db: Session = Depends(get_db)):
    convs = db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.updated_at.desc()).all()
    return [
        {
            "id": c.id,
            "title": c.title,
            "status": c.status,
            "updated_at": c.updated_at.isoformat() if c.updated_at else None
        }
        for c in convs
    ]

@router.post("/chat/conversations")
def create_new_conversation(title: Optional[str] = "New Chat", user_id: int = 1, db: Session = Depends(get_db)):
    conv = Conversation(user_id=user_id, title=title or "New Chat")
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return {
        "id": conv.id,
        "title": conv.title,
        "status": conv.status,
        "created_at": conv.created_at.isoformat()
    }

@router.get("/chat/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: int, user_id: int = 1, db: Session = Depends(get_db)):
    msgs = db.query(ConversationMessage).filter(ConversationMessage.conversation_id == conversation_id).order_by(ConversationMessage.created_at.asc()).all()
    return [
        {
            "id": m.id,
            "sender": m.sender,
            "text": m.message,
            "type": m.message_type or "text",
            "intent": m.intent,
            "payload": m.metadata_json.get("payload") if m.metadata_json else None,
            "quick_replies": m.metadata_json.get("quick_replies") if m.metadata_json else None,
            "created_at": m.created_at.isoformat()
        }
        for m in msgs
    ]

@router.delete("/chat/conversations/{conversation_id}")
def delete_conversation(conversation_id: int, user_id: int = 1, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conv)
    db.commit()
    return {"message": "Conversation deleted successfully"}
