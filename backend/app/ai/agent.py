import json
import logging
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session

from app.models.conversation import Conversation, ConversationMessage
from app.models.ticket import Event
from app.ai.provider import get_ai_provider, AIProvider
from app.ai.tool_registry import tool_registry
from app.ai.conversation_memory import memory_manager, ConversationState
from app.ai.context_builder import build_ai_context
from app.ai.response_builder import build_agent_response
from app.ai.safety import detect_prompt_injection, sanitize_user_input
from app.ai.schemas import AgentResponse

logger = logging.getLogger("chatassist.ai.agent")

MAX_TOOL_ROUNDS = 8

class ChatAssistAgent:
    def __init__(self, provider: Optional[AIProvider] = None):
        self.provider = provider or get_ai_provider()

    def process_message(
        self,
        user_message: str,
        user_id: int,
        conversation_id: int,
        db: Session,
        user_role: str = "customer",
        event_type: str = "user_message",
        payload: Optional[Dict[str, Any]] = None
    ) -> AgentResponse:
        clean_input = sanitize_user_input(user_message or "")

        # 1. Prompt Injection Defense
        is_injection, injection_msg = detect_prompt_injection(clean_input)
        state = memory_manager.get_or_create_state(conversation_id, user_id, db=db)

        if is_injection:
            return build_agent_response(
                message=injection_msg,
                state=state,
                intent="security_refusal"
            )

        # 2. Retrieve history and construct initial context
        history = memory_manager.get_recent_messages(conversation_id, db=db, limit=8)
        current_messages = build_ai_context(state, history, user_role=user_role, db=db)

        # Append current user message
        if clean_input:
            current_messages.append({"role": "user", "content": clean_input})

        tools_declarations = tool_registry.get_openai_tools()

        primary_tool_name: Optional[str] = None
        primary_tool_data: Optional[Dict[str, Any]] = None
        final_text: str = ""

        # 3. Tool Loop
        for round_idx in range(MAX_TOOL_ROUNDS):
            try:
                response = self.provider.chat(current_messages, tools=tools_declarations)
            except Exception as e:
                logger.error(f"AI Provider error in round {round_idx}: {e}")
                final_text = "I'm having trouble processing that right now. Please try again in a moment."
                break

            tool_calls = response.get("tool_calls")
            assistant_content = response.get("content")

            if assistant_content:
                final_text = assistant_content

            if not tool_calls:
                # No more tools needed, assistant completed its reasoning
                break

            # Execute returned tool calls
            for tc in tool_calls:
                t_name = tc.get("name")
                t_args = tc.get("arguments", {})

                logger.info(f"Executing tool {t_name} with args {t_args}")
                t_res = tool_registry.execute_tool(
                    name=t_name,
                    raw_args=t_args,
                    db=db,
                    user_id=user_id,
                    conversation_id=conversation_id
                )

                tool_data = t_res.data or {}

                # Update conversation session state from tool output
                self._update_state_from_tool(state, t_name, tool_data)

                if not primary_tool_name and t_res.success:
                    primary_tool_name = t_name
                    primary_tool_data = tool_data

                # Append tool execution turn to messages for next round
                current_messages.append({
                    "role": "assistant",
                    "content": f"Calling tool {t_name}",
                    "tool_calls": [tc]
                })
                current_messages.append({
                    "role": "tool",
                    "name": t_name,
                    "content": json.dumps(tool_data if t_res.success else (t_res.error or {}))
                })

        if not final_text:
            final_text = "I've processed your request."

        # 4. Build Structured Agent Response
        agent_resp = build_agent_response(
            message=final_text,
            state=state,
            primary_tool_name=primary_tool_name,
            primary_tool_data=primary_tool_data
        )

        return agent_resp

    def _update_state_from_tool(self, state: ConversationState, tool_name: str, tool_data: Dict[str, Any]):
        if tool_name == "search_events":
            events = tool_data.get("events", [])
            state.last_event_result_ids = [e["id"] for e in events]
            state.last_action = "SEARCH_EVENTS"

        elif tool_name in ["create_booking_draft", "update_booking_draft"]:
            state.selected_event_id = tool_data.get("event_id")
            state.selected_tier_name = tool_data.get("ticket_type")
            state.quantity = tool_data.get("quantity", 1)
            state.booking_draft_id = tool_data.get("draft_id")
            state.last_action = "BOOKING_HELD"

        elif tool_name == "remove_booking_item":
            state.reset_booking()
            state.last_action = "BOOKING_CANCELLED"

        elif tool_name == "create_payment_order":
            state.payment_status = "PENDING"
            state.last_action = "PAYMENT_INITIATED"

        elif tool_name == "apply_promo_code":
            state.promo_code = tool_data.get("promo_code")
            state.last_action = "PROMO_APPLIED"

# Global singleton agent
chat_agent = ChatAssistAgent()
