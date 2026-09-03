import time
import logging
from typing import Dict, Any, Callable, Type, List, Optional
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai.schemas import (
    ToolResult,
    SearchEventsArgs,
    GetEventDetailsArgs,
    GetEventTiersArgs,
    CompareEventsArgs,
    CheckAvailabilityArgs,
    GetTicketPriceArgs,
    CreateBookingDraftArgs,
    UpdateBookingDraftArgs,
    RemoveBookingItemArgs,
    ApplyPromoCodeArgs,
    RemovePromoCodeArgs,
    CalculateBookingTotalArgs,
    CreatePaymentOrderArgs,
    GetBookingStatusArgs,
    GetUserBookingsArgs,
    GetUserTicketsArgs,
    GetTicketDetailsArgs,
    CancelBookingArgs,
    TransferTicketArgs,
    JoinWaitlistArgs,
    LeaveWaitlistArgs,
    GetWaitlistStatusArgs,
    GetEventRecommendationsArgs,
)
from app.ai import tools

logger = logging.getLogger("chatassist.ai.tools")

class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        args_schema: Type[BaseModel],
        func: Callable
    ):
        self.name = name
        self.description = description
        self.args_schema = args_schema
        self.func = func

    def to_openai_dict(self) -> Dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.args_schema.model_json_schema()
            }
        }

    def to_gemini_dict(self) -> Dict[str, Any]:
        schema = self.args_schema.model_json_schema()
        # Clean $defs if any for Gemini
        return {
            "name": self.name,
            "description": self.description,
            "parameters": schema
        }

class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(self, name: str, description: str, args_schema: Type[BaseModel], func: Callable):
        self._tools[name] = ToolDefinition(name, description, args_schema, func)

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def get_openai_tools(self) -> List[Dict[str, Any]]:
        return [t.to_openai_dict() for t in self._tools.values()]

    def get_gemini_tools(self) -> List[Dict[str, Any]]:
        return [t.to_gemini_dict() for t in self._tools.values()]

    def execute_tool(
        self,
        name: str,
        raw_args: Dict[str, Any],
        db: Session,
        user_id: int = 1,
        conversation_id: Optional[int] = None
    ) -> ToolResult:
        tool_def = self.get_tool(name)
        if not tool_def:
            return ToolResult(success=False, error={"code": "TOOL_NOT_FOUND", "message": f"Tool '{name}' not found."})

        # Validate arguments using Pydantic schema
        try:
            validated = tool_def.args_schema(**raw_args)
            validated_dict = validated.model_dump(exclude_unset=True)
        except Exception as e:
            return ToolResult(success=False, error={"code": "INVALID_ARGUMENTS", "message": f"Validation failed for {name}: {str(e)}"})

        start_t = time.time()
        try:
            # Dispatch according to tool function signature
            kwargs = dict(validated_dict)
            func_code = tool_def.func.__code__
            accepted_params = func_code.co_varnames[:func_code.co_argcount]

            if "db" in accepted_params:
                kwargs["db"] = db
            if "user_id" in accepted_params:
                kwargs["user_id"] = user_id
            if "conversation_id" in accepted_params:
                kwargs["conversation_id"] = conversation_id

            res = tool_def.func(**kwargs)
            duration_ms = round((time.time() - start_t) * 1000, 2)
            logger.info(f"Tool {name} executed in {duration_ms}ms (success={res.success})")
            return res
        except Exception as e:
            duration_ms = round((time.time() - start_t) * 1000, 2)
            logger.error(f"Tool {name} failed in {duration_ms}ms: {str(e)}")
            return ToolResult(success=False, error={"code": "EXECUTION_ERROR", "message": str(e)})

    def _register_default_tools(self):
        self.register(
            name="search_events",
            description="Search upcoming live events by keyword, category (e.g. Technology, Comedy, Music, Workshop), city (e.g. Bengaluru, Mangaluru), max price, or timeframe.",
            args_schema=SearchEventsArgs,
            func=tools.tool_search_events
        )
        self.register(
            name="get_event_details",
            description="Get complete event details, venue address, start/end time, description, and available ticket tiers for a specific event ID.",
            args_schema=GetEventDetailsArgs,
            func=tools.tool_get_event_details
        )
        self.register(
            name="get_event_tiers",
            description="Get all available ticket tiers, prices, and limits for an event ID.",
            args_schema=GetEventTiersArgs,
            func=tools.tool_get_event_tiers
        )
        self.register(
            name="compare_events",
            description="Compare two events side-by-side on price, date, category, venue, and available tiers.",
            args_schema=CompareEventsArgs,
            func=tools.tool_compare_events
        )
        self.register(
            name="check_ticket_availability",
            description="Check authoritative real-time seat availability for an event or specific tier.",
            args_schema=CheckAvailabilityArgs,
            func=tools.tool_check_ticket_availability
        )
        self.register(
            name="calculate_booking_total",
            description="Calculate exact subtotal, 18% GST (CGST/SGST), optional promo discounts, and final total without placing a reservation.",
            args_schema=CalculateBookingTotalArgs,
            func=tools.tool_calculate_booking_total
        )
        self.register(
            name="create_booking_draft",
            description="Create a real booking draft and place an atomic 10-minute hold on inventory in Redis/database.",
            args_schema=CreateBookingDraftArgs,
            func=tools.tool_create_booking_draft
        )
        self.register(
            name="update_booking_draft",
            description="Update quantity or tier on the active 10-minute booking reservation.",
            args_schema=UpdateBookingDraftArgs,
            func=tools.tool_update_booking_draft
        )
        self.register(
            name="remove_booking_item",
            description="Cancel active reservation and immediately release held seats back into inventory.",
            args_schema=RemoveBookingItemArgs,
            func=tools.tool_remove_booking_item
        )
        self.register(
            name="apply_promo_code",
            description="Validate and apply a coupon or promo code (e.g. STUDENT15) to the active booking draft.",
            args_schema=ApplyPromoCodeArgs,
            func=tools.tool_apply_promo_code
        )
        self.register(
            name="create_payment_order",
            description="Prepare an authoritative Razorpay payment order for the active booking draft so the user can complete payment.",
            args_schema=CreatePaymentOrderArgs,
            func=tools.tool_create_payment_order
        )
        self.register(
            name="get_user_tickets",
            description="Get the authenticated user's confirmed event tickets, QR code tokens, and pass status.",
            args_schema=GetUserTicketsArgs,
            func=tools.tool_get_user_tickets
        )
        self.register(
            name="cancel_booking",
            description="Cancel a confirmed ticket and initiate a refund according to event policy.",
            args_schema=CancelBookingArgs,
            func=tools.tool_cancel_booking
        )
        self.register(
            name="transfer_ticket",
            description="Transfer a confirmed ticket to a recipient email address and generate a new secure pass.",
            args_schema=TransferTicketArgs,
            func=tools.tool_transfer_ticket
        )
        self.register(
            name="join_waitlist",
            description="Join the waitlist for a sold-out event or tier.",
            args_schema=JoinWaitlistArgs,
            func=tools.tool_join_waitlist
        )
        self.register(
            name="get_event_recommendations",
            description="Get curated event recommendations based on category interest and popularity.",
            args_schema=GetEventRecommendationsArgs,
            func=tools.tool_get_event_recommendations
        )

# Global singleton registry
tool_registry = ToolRegistry()
