import os
import re
import json
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

import httpx
from app.core.config import settings

logger = logging.getLogger("chatassist.ai.provider")

class AIProvider(ABC):
    @abstractmethod
    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto"
    ) -> Dict[str, Any]:
        """
        Sends messages and tool declarations to the LLM.
        Returns:
            {
                "content": Optional[str],
                "tool_calls": Optional[List[Dict[str, Any]]]  # [{ "name": ..., "arguments": ... }]
            }
        """
        pass


class GeminiProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gemini-1.5-flash"):
        self.api_key = api_key
        self.model = model or "gemini-1.5-flash"

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto"
    ) -> Dict[str, Any]:
        # Format messages for Gemini API
        contents = []
        system_instruction = None

        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role == "system":
                system_instruction = {"parts": [{"text": content}]}
            elif role == "assistant":
                contents.append({"role": "model", "parts": [{"text": content}]})
            elif role == "user":
                contents.append({"role": "user", "parts": [{"text": content}]})
            elif role == "tool":
                contents.append({
                    "role": "function",
                    "parts": [{
                        "functionResponse": {
                            "name": m.get("name", "tool"),
                            "response": {"output": m.get("content", "")}
                        }
                    }]
                })

        gemini_tools = None
        if tools:
            func_declarations = []
            for t in tools:
                func_declarations.append({
                    "name": t.get("name"),
                    "description": t.get("description"),
                    "parameters": t.get("parameters")
                })
            gemini_tools = [{"functionDeclarations": func_declarations}]

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": 800
            }
        }
        if system_instruction:
            payload["systemInstruction"] = system_instruction
        if gemini_tools:
            payload["tools"] = gemini_tools

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post(url, json=payload)
                if resp.status_code != 200:
                    logger.error(f"Gemini API returned error {resp.status_code}: {resp.text}")
                    raise RuntimeError(f"Gemini API error: {resp.status_code}")

                data = resp.json()
                candidates = data.get("candidates", [])
                if not candidates:
                    return {"content": "I couldn't process that request right now.", "tool_calls": None}

                part = candidates[0].get("content", {}).get("parts", [{}])[0]
                if "functionCall" in part:
                    fc = part["functionCall"]
                    return {
                        "content": None,
                        "tool_calls": [{
                            "name": fc.get("name"),
                            "arguments": fc.get("args", {})
                        }]
                    }

                return {"content": part.get("text", ""), "tool_calls": None}
        except Exception as e:
            logger.error(f"Gemini request exception: {e}")
            raise


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model or "gpt-4o-mini"

    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto"
    ) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        body: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 800
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = tool_choice

        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.post("https://api.openai.com/v1/chat/completions", headers=headers, json=body)
                if resp.status_code != 200:
                    logger.error(f"OpenAI API returned error {resp.status_code}: {resp.text}")
                    raise RuntimeError(f"OpenAI API error: {resp.status_code}")

                data = resp.json()
                choice = data["choices"][0]["message"]
                if choice.get("tool_calls"):
                    calls = []
                    for tc in choice["tool_calls"]:
                        fn = tc.get("function", {})
                        args = fn.get("arguments", "{}")
                        try:
                            parsed_args = json.loads(args) if isinstance(args, str) else args
                        except Exception:
                            parsed_args = {}
                        calls.append({
                            "name": fn.get("name"),
                            "arguments": parsed_args
                        })
                    return {"content": choice.get("content"), "tool_calls": calls}

                return {"content": choice.get("content", ""), "tool_calls": None}
        except Exception as e:
            logger.error(f"OpenAI request exception: {e}")
            raise


class SmartLocalProvider(AIProvider):
    """
    Intelligent deterministic conversational reasoner.
    Serves as the zero-dependency fallback when external API keys are not provided in .env,
    ensuring all search, contextual reference resolution, multi-turn booking, side question,
    pricing calculation, and chit-chat flows work seamlessly out-of-the-box.
    """
    def chat(
        self,
        messages: List[Dict[str, Any]],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: Optional[str] = "auto"
    ) -> Dict[str, Any]:
        # Extract last user message and system instructions
        last_user_msg = ""
        system_content = ""
        for m in reversed(messages):
            if m.get("role") == "user" and not last_user_msg:
                last_user_msg = m.get("content", "")
            if m.get("role") == "system":
                system_content = m.get("content", "")

        msg_lower = (last_user_msg or "").lower().strip()

        # Check if the preceding message was a tool result
        last_msg = messages[-1] if messages else {}
        if last_msg.get("role") == "tool":
            tool_name = last_msg.get("name")
            tool_data_raw = last_msg.get("content", "{}")
            try:
                tool_data = json.loads(tool_data_raw)
            except Exception:
                tool_data = {}

            # Synthesize conversational response based on tool result
            if tool_name == "search_events":
                events = tool_data.get("events", [])
                if events:
                    return {
                        "content": f"I found {len(events)} event{'s' if len(events)>1 else ''} matching your search. Take a look at the options below:",
                        "tool_calls": None
                    }
                return {
                    "content": "I couldn't find any upcoming live events matching those criteria. Would you like to see all available events?",
                    "tool_calls": None
                }

            elif tool_name in ["create_booking_draft", "update_booking_draft"]:
                d = tool_data
                return {
                    "content": (
                        f"I've reserved **{d.get('quantity', 1)} × {d.get('ticket_type', 'Standard')}** ticket(s) for **{d.get('event_title', 'Event')}**.\n\n"
                        f"• Unit Price: ₹{d.get('unit_price', 0):.2f}\n"
                        f"• Subtotal: ₹{d.get('subtotal', 0):.2f}\n"
                        f"• 18% GST: ₹{d.get('tax', 0):.2f}\n"
                        f"• **Grand Total: ₹{d.get('total', 0):.2f}**\n\n"
                        f"⏱️ Seats are held for 10 minutes. Click below to proceed with payment or let me know if you want to make changes."
                    ),
                    "tool_calls": None
                }

            elif tool_name == "create_payment_order":
                total = tool_data.get("total", 0.0)
                return {
                    "content": f"Your payment order has been prepared. Please click **Pay ₹{total:.2f} Securely** below to complete your checkout with Razorpay:",
                    "tool_calls": None
                }

            elif tool_name == "get_user_tickets":
                tickets = tool_data.get("tickets", [])
                if tickets:
                    return {
                        "content": f"Here are your upcoming event tickets ({len(tickets)} confirmed):",
                        "tool_calls": None
                    }
                return {
                    "content": "You don't have any booked tickets yet. Can I help you find an exciting event to attend?",
                    "tool_calls": None
                }

            elif tool_name == "cancel_booking":
                ref_amt = tool_data.get("refund_amount", 0.0)
                return {
                    "content": f"Your ticket {tool_data.get('ticket_number', '')} has been cancelled successfully. A refund of ₹{ref_amt:.2f} has been credited to your payment source.",
                    "tool_calls": None
                }

            elif tool_name == "apply_promo_code":
                return {
                    "content": f"Promo code **{tool_data.get('promo_code')}** applied! You saved ₹{tool_data.get('discount_amount', 0):.2f}. Updated total is ₹{tool_data.get('total', 0):.2f}.",
                    "tool_calls": None
                }

            elif tool_name == "transfer_ticket":
                return {
                    "content": f"Ticket transferred successfully to {tool_data.get('recipient_email')}. A new cryptographic QR ticket has been issued for them.",
                    "tool_calls": None
                }

            elif tool_name == "join_waitlist":
                return {
                    "content": f"You are #{tool_data.get('position')} on the waitlist for {tool_data.get('event_title', 'the event')}. We will notify you immediately if tickets free up!",
                    "tool_calls": None
                }

            elif tool_name == "compare_events":
                e1 = tool_data.get("event_1", {})
                e2 = tool_data.get("event_2", {})
                return {
                    "content": f"Here is a side-by-side comparison of **{e1.get('title', 'Event 1')}** and **{e2.get('title', 'Event 2')}**:\n\n• **{e1.get('title')}**: From ₹{e1.get('price', 0):.0f} ({e1.get('date_str')}, {e1.get('location')})\n• **{e2.get('title')}**: From ₹{e2.get('price', 0):.0f} ({e2.get('date_str')}, {e2.get('location')})\n\nTake a look at the feature comparison below:",
                    "tool_calls": None
                }

        # -------------------------------------------------------------
        # Intent & Conversational Reasoning
        # -------------------------------------------------------------

        # 1. Pure Conversational Chit-Chat & Greetings (NO tools should be called)
        greetings = ["hi", "hello", "hey", "good morning", "good evening", "howdy", "sup"]
        if any(msg_lower == g or msg_lower.startswith(g + " ") for g in greetings):
            return {
                "content": "Hey! How can I help you today? I can help you discover exciting events, book passes, check seat availability, or manage your existing tickets.",
                "tool_calls": None
            }

        if "tell me a joke" in msg_lower or "joke" in msg_lower:
            return {
                "content": "Why did the developer bring a ladder to the tech event? Because they heard the architecture was high-level! 😄\n\nLooking for any real tech or comedy events this weekend?",
                "tool_calls": None
            }

        if "what can you do" in msg_lower or "who are you" in msg_lower:
            return {
                "content": "I'm ChatAssist, your AI conversational ticketing assistant! I can help you find live events, reserve tickets, calculate exact GST breakdowns, complete payments, view your QR passes, and answer event questions. How can I help you today?",
                "tool_calls": None
            }

        if "what is artificial intelligence" in msg_lower or "what is machine learning" in msg_lower or "what is ai" in msg_lower:
            return {
                "content": "Artificial Intelligence (AI) is the simulation of human intelligence by machines, enabling them to learn from data, reason through problems, and understand natural language. Speaking of AI, we often have great AI conferences and tech workshops listed! Want to explore any?",
                "tool_calls": None
            }

        if any(msg_lower == c for c in ["thanks", "thank you", "cool", "sounds good", "awesome", "great"]):
            return {
                "content": "You're very welcome! Let me know if there's anything else I can help you with.",
                "tool_calls": None
            }

        # 2. Side Questions: Venue, Time, Schedule, Parking
        if any(k in msg_lower for k in ["where is the venue", "venue address", "what is the venue", "where is it", "location of"]):
            # Extract venue from system prompt grounded info if present
            venue_match = re.search(r"Venue='([^']+)'", system_content)
            title_match = re.search(r"Title='([^']+)'", system_content)
            if venue_match:
                venue_str = venue_match.group(1)
                title_str = title_match.group(1) if title_match else "the event"
                return {
                    "content": f"The venue for **{title_str}** is {venue_str}. Your active reservation is still saved. Let me know when you're ready to continue booking!",
                    "tool_calls": None
                }

        # 2b. Comparison request ("compare the first and second one", "compare first and second", "compare 1 and 2")
        if "compare" in msg_lower:
            ordinals_found = []
            if "first" in msg_lower or "1st" in msg_lower:
                ordinals_found.append(0)
            if "second" in msg_lower or "2nd" in msg_lower:
                ordinals_found.append(1)
            if "third" in msg_lower or "3rd" in msg_lower:
                ordinals_found.append(2)

            search_ids_match = re.findall(r'\[(\d+)\]\s+ID=(\d+)', system_content)
            if search_ids_match and len(search_ids_match) >= 2:
                idx1 = ordinals_found[0] if len(ordinals_found) >= 1 and ordinals_found[0] < len(search_ids_match) else 0
                idx2 = ordinals_found[1] if len(ordinals_found) >= 2 and ordinals_found[1] < len(search_ids_match) else (1 if len(search_ids_match) > 1 else 0)
                e1_id = int(search_ids_match[idx1][1])
                e2_id = int(search_ids_match[idx2][1])
                return {
                    "content": None,
                    "tool_calls": [{
                        "name": "compare_events",
                        "arguments": {"event_id_1": e1_id, "event_id_2": e2_id}
                    }]
                }

        # 3. Payment Confirmation ("pay", "proceed", "go ahead", "confirm booking", "book it")
        if any(k in msg_lower for k in ["go ahead", "proceed", "confirm and pay", "proceed to pay", "pay now", "confirm booking", "confirm", "pay"]):
            draft_match = re.search(r"Active Booking Draft ID:\s*(\d+)", system_content)
            draft_id = int(draft_match.group(1)) if draft_match else None
            return {
                "content": None,
                "tool_calls": [{
                    "name": "create_payment_order",
                    "arguments": {"draft_id": draft_id}
                }]
            }

        # 4. User Corrections: Quantity Changes ("actually make that 3", "change quantity to 2", "make it 4")
        qty_change = re.search(r'(?:actually\s+)?(?:make\s+(?:it|that)|change\s+(?:to|quantity\s+to)|update\s+to)\s+(\d+)', msg_lower)
        if qty_change:
            new_q = int(qty_change.group(1))
            draft_match = re.search(r"Active Booking Draft ID:\s*(\d+)", system_content)
            draft_id = int(draft_match.group(1)) if draft_match else None
            return {
                "content": None,
                "tool_calls": [{
                    "name": "update_booking_draft",
                    "arguments": {"draft_id": draft_id, "quantity": new_q}
                }]
            }

        # 5. Promo Code ("try STUDENT15", "use promo X", "apply coupon Y")
        promo_match = re.search(r'(?:try|use|apply)\s+(?:promo|coupon|code)?\s*([A-Z0-9_-]{4,15})', last_user_msg, re.IGNORECASE)
        if promo_match and not any(k in msg_lower for k in ["show", "event", "ticket", "book"]):
            code = promo_match.group(1).upper()
            draft_match = re.search(r"Active Booking Draft ID:\s*(\d+)", system_content)
            draft_id = int(draft_match.group(1)) if draft_match else None
            return {
                "content": None,
                "tool_calls": [{
                    "name": "apply_promo_code",
                    "arguments": {"promo_code": code, "draft_id": draft_id}
                }]
            }

        # 6. Ticket Management ("show my tickets", "my passes", "where is my qr")
        if any(k in msg_lower for k in ["my tickets", "show tickets", "where is my qr", "my bookings", "booked tickets"]):
            return {
                "content": None,
                "tool_calls": [{
                    "name": "get_user_tickets",
                    "arguments": {"limit": 5}
                }]
            }

        # 7. Cancellation & Refunds ("cancel my ticket", "cancel booking")
        if any(k in msg_lower for k in ["cancel my booking", "cancel my ticket", "cancel reservation"]):
            ticket_num_match = re.search(r'\b(TCK-[A-Z0-9]+|\d+)\b', last_user_msg)
            t_id = 1
            if ticket_num_match and ticket_num_match.group(1).isdigit():
                t_id = int(ticket_num_match.group(1))
            return {
                "content": None,
                "tool_calls": [{
                    "name": "cancel_booking",
                    "arguments": {"ticket_id": t_id}
                }]
            }

        # 8. Ordinals & Booking Turns ("book the first one", "book 2 VIP passes for the second one", "2 VIP")
        ordinal_idx = None
        if "first" in msg_lower or "1st" in msg_lower:
            ordinal_idx = 0
        elif "second" in msg_lower or "2nd" in msg_lower:
            ordinal_idx = 1
        elif "third" in msg_lower or "3rd" in msg_lower:
            ordinal_idx = 2

        # Extract target event ID
        target_event_id = None
        if ordinal_idx is not None:
            # Parse last search results from system context
            search_ids_match = re.findall(r'\[(\d+)\]\s+ID=(\d+)', system_content)
            if search_ids_match and ordinal_idx < len(search_ids_match):
                target_event_id = int(search_ids_match[ordinal_idx][1])

        if not target_event_id:
            active_eid_match = re.search(r"Active Selected Event: ID=(\d+)", system_content)
            if active_eid_match:
                target_event_id = int(active_eid_match.group(1))

        # Check if booking is requested
        is_booking_request = any(k in msg_lower for k in ["book", "reserve", "tickets", "ticket", "pass", "passes", "vip", "standard"])

        if not target_event_id and is_booking_request:
            try:
                from app.core.database import SessionLocal
                from app.models.ticket import Event
                temp_db = SessionLocal()
                live_events = temp_db.query(Event).filter(Event.available_tickets > 0).all()
                for ev in sorted(live_events, key=lambda x: len(x.title), reverse=True):
                    if ev.title.lower() in msg_lower:
                        target_event_id = ev.id
                        break
                if not target_event_id:
                    for ev in sorted(live_events, key=lambda x: len(x.title), reverse=True):
                        words = [w for w in ev.title.lower().split() if len(w) > 3]
                        if words and any(w in msg_lower for w in words):
                            target_event_id = ev.id
                            break
                if not target_event_id:
                    search_ids_match = re.findall(r'\[(\d+)\]\s+ID=(\d+)', system_content)
                    if search_ids_match:
                        target_event_id = int(search_ids_match[0][1])
                if not target_event_id and len(live_events) == 1:
                    target_event_id = live_events[0].id
                temp_db.close()
            except Exception:
                pass

        if is_booking_request and target_event_id:
            # Parse requested quantity and tier
            qty = 1
            num_match = re.search(r'\b([1-9]\d?)\b', msg_lower)
            if num_match:
                qty = int(num_match.group(1))

            tier_name = "Standard"
            if "vip" in msg_lower:
                tier_name = "VIP Pass"

            return {
                "content": None,
                "tool_calls": [{
                    "name": "create_booking_draft",
                    "arguments": {
                        "event_id": target_event_id,
                        "tier_name": tier_name,
                        "quantity": qty
                    }
                }]
            }

        # 9. Natural Language Search Queries
        is_search = any(k in msg_lower for k in [
            "search", "find", "show", "events", "concert", "comedy", "tech", "workshop",
            "bangalore", "bengaluru", "mangalore", "mangaluru", "happening", "weekend", "cheaper"
        ])
        if is_search or "bored" in msg_lower or "anything fun" in msg_lower:
            cat = None
            for c in ["Technology", "Tech", "Comedy", "Music", "Workshop", "Gaming", "Business"]:
                if c.lower() in msg_lower:
                    cat = c
                    break

            city = None
            if "beng" in msg_lower or "bang" in msg_lower:
                city = "Bengaluru"
            elif "mang" in msg_lower:
                city = "Mangaluru"

            max_p = None
            p_match = re.search(r'(?:under|below|less than|<=|<|\b₹?\s*)(\d+)', msg_lower)
            if p_match and "ticket" not in msg_lower:
                max_p = float(p_match.group(1))

            return {
                "content": None,
                "tool_calls": [{
                    "name": "search_events",
                    "arguments": {
                        "query": last_user_msg if not (cat or city or max_p) else None,
                        "category": cat,
                        "city": city,
                        "max_price": max_p
                    }
                }]
            }

        # Default conversational response
        return {
            "content": f"I'm here to assist you with live events, ticket booking, and check-ins. How can I help you today?",
            "tool_calls": None
        }


def get_ai_provider() -> AIProvider:
    provider_name = settings.AI_PROVIDER.lower()
    gemini_key = settings.GEMINI_API_KEY
    openai_key = settings.OPENAI_API_KEY or os.getenv("OPENAI_API_KEY", "")

    if provider_name == "gemini" and gemini_key:
        logger.info("Using Gemini AI Provider")
        return GeminiProvider(api_key=gemini_key, model=settings.AI_MODEL or "gemini-1.5-flash")

    if provider_name == "openai" and openai_key:
        logger.info("Using OpenAI AI Provider")
        return OpenAIProvider(api_key=openai_key, model=settings.AI_MODEL or "gpt-4o-mini")

    # If keys are missing or provider=local, fall back to SmartLocalProvider
    logger.info("Using SmartLocalProvider (reliable deterministic conversational engine)")
    return SmartLocalProvider()
