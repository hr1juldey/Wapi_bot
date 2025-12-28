"""Booking confirmation and creation node group.

Handles:
- Price calculation
- Showing booking summary
- Processing confirmation (via domain node)
- Creating booking
- Success/error messages

Replaces 5 old nodes:
- calculate_price
- send_confirmation
- extract_confirmation
- create_booking
- send_success/cancelled
"""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from nodes.atomic.send_media import node as send_media_node
from nodes.atomic.call_frappe import node as call_frappe_node
from nodes.message_builders.booking_confirmation import BookingConfirmationBuilder
from nodes.message_builders.payment_instructions import build_payment_instructions_caption
from nodes.payments import generate_qr_node, schedule_reminders_node
from nodes.routing.resume_router import create_resume_router
from nodes.domain import calculate_booking_price
from nodes.transformers.extract_booking_params import ExtractBookingParams
from clients.frappe_yawlit import get_yawlit_client
from core.config import settings

logger = logging.getLogger(__name__)


async def calculate_price(state: BookingState) -> BookingState:
    """Calculate real price using domain node."""
    return await calculate_booking_price.node(state)


async def send_confirmation(state: BookingState) -> BookingState:
    """Send booking confirmation for user approval, then pause for input."""
    result = await send_message_node(state, BookingConfirmationBuilder())

    # Pause and wait for user's confirmation
    result["should_proceed"] = False
    result["current_step"] = "awaiting_booking_confirmation"
    return result


async def extract_confirmation(state: BookingState) -> BookingState:
    """Extract YES/NO confirmation using domain extraction node."""
    # Use domain node for better regex patterns and LLM fallback
    from nodes.extraction import extract_confirmation as extract_confirmation_node
    result = await extract_confirmation_node.node(state, field_path="confirmed")

    logger.info(f"🔍 Confirmation extracted: {result.get('confirmed')}")
    return result


async def route_confirmation(state: BookingState) -> str:
    """Route based on user confirmation."""
    confirmed = state.get("confirmed")
    if confirmed is True:
        return "confirmed"
    elif confirmed is False:
        return "cancelled"
    else:
        return "unclear"


async def create_booking(state: BookingState) -> BookingState:
    """Create booking using transformer for params extraction."""
    client = get_yawlit_client()

    # Extract booking params using transformer
    transformer = ExtractBookingParams()
    booking_params = transformer(None, state)

    logger.info("📝 Creating booking via create_booking_by_phone...")
    result = await call_frappe_node(
        state,
        client.booking_create.create_booking_by_phone,
        "booking_api_response",
        state_extractor=lambda s: booking_params
    )

    # Extract booking data from response
    api_response = result.get("booking_api_response", {})
    message = api_response.get("message", {})

    result["booking_response"] = message
    result["booking_id"] = message.get("booking_id", "Unknown")
    result["booking_data"] = message.get("booking_data", {})

    logger.info(f"✅ Booking created: {result.get('booking_id')}")
    logger.info(f"📋 Booking ID in state: {result.get('booking_id')}")
    return result


async def generate_payment_qr(state: BookingState) -> BookingState:
    """Generate UPI QR code for payment."""
    amount = state.get("total_price")
    booking_id = state.get("booking_id", "Unknown")
    logger.info(f"🔍 DEBUG: State has booking_id key: {'booking_id' in state}")
    logger.info(f"🔍 DEBUG: booking_id value: {repr(state.get('booking_id'))}")
    logger.info(f"🔍 DEBUG: booking_response value: {repr(state.get('booking_response'))}")
    logger.info(f"🔍 Generating QR for booking: {booking_id}")

    return await generate_qr_node(
        state,
        amount=amount,
        transaction_note=f"Yawlit Booking {booking_id}",
    )


async def schedule_payment_reminders(state: BookingState) -> BookingState:
    """Schedule payment reminders (non-blocking)."""
    return await schedule_reminders_node(state, on_failure="log")


async def send_qr_message(state: BookingState) -> BookingState:
    """Send QR code IMAGE with professional payment instructions."""

    def qr_media_builder(s):
        session_id = s.get("payment_session_id")
        amount = s.get("payment_amount", 0)

        # Construct public URL for QR image
        media_url = f"{settings.public_base_url}/api/v1/qr/{session_id}.png"

        # Build professional payment instructions with all payment modes
        caption = build_payment_instructions_caption(amount)

        return {
            "media_type": "image",
            "media_url": media_url,
            "caption": caption
        }

    return await send_media_node(state, qr_media_builder)


async def send_success(state: BookingState) -> BookingState:
    """Send booking success message."""

    def success_message(s):
        booking_id = s.get("booking_id", "Unknown")
        return f"✅ Booking confirmed!\n\nYour booking ID is: {booking_id}\n\nWe'll send you a confirmation shortly. Thank you for choosing Yawlit!"

    return await send_message_node(state, success_message)


async def send_cancelled(state: BookingState) -> BookingState:
    """Send booking cancelled message."""
    def cancelled_message(s):
        return "❌ Booking cancelled. Feel free to start a new booking anytime!"

    return await send_message_node(state, cancelled_message)


async def send_unclear(state: BookingState) -> BookingState:
    """Send message for unclear confirmation."""
    def unclear_message(s):
        return "Please reply with YES to confirm or NO to cancel the booking."

    result = await send_message_node(state, unclear_message)
    result["should_proceed"] = False  # Stop and wait for next user message
    result["current_step"] = "awaiting_booking_confirmation"  # Resume here on next message
    return result


# Create resume router for entry point
route_booking_entry = create_resume_router(
    awaiting_step="awaiting_booking_confirmation",
    resume_node="extract_confirmation",
    fresh_node="calculate_price",
    readiness_check=lambda s: s.get("total_price") is not None,
    router_name="booking_entry"
)


def create_booking_group() -> StateGraph:
    """Create booking confirmation and creation node group."""
    workflow = StateGraph(BookingState)

    # Add nodes
    workflow.add_node("entry", lambda s: s)  # Pass-through entry
    workflow.add_node("calculate_price", calculate_price)
    workflow.add_node("send_confirmation", send_confirmation)
    workflow.add_node("extract_confirmation", extract_confirmation)
    workflow.add_node("create_booking", create_booking)
    workflow.add_node("generate_payment_qr", generate_payment_qr)
    workflow.add_node("schedule_payment_reminders", schedule_payment_reminders)
    workflow.add_node("send_qr_message", send_qr_message)
    workflow.add_node("send_success", send_success)
    workflow.add_node("send_cancelled", send_cancelled)
    workflow.add_node("send_unclear", send_unclear)

    # Start at entry for routing
    workflow.set_entry_point("entry")

    # Route based on resume state
    workflow.add_conditional_edges(
        "entry",
        route_booking_entry,
        {
            "calculate_price": "calculate_price",
            "extract_confirmation": "extract_confirmation"
        }
    )

    workflow.add_edge("calculate_price", "send_confirmation")
    # After showing confirmation, END and wait for user input (pause)
    workflow.add_edge("send_confirmation", END)

    workflow.add_conditional_edges(
        "extract_confirmation",
        route_confirmation,
        {
            "confirmed": "create_booking",
            "cancelled": "send_cancelled",
            "unclear": "send_unclear"
        }
    )

    # Payment flow (after booking created)
    workflow.add_edge("create_booking", "generate_payment_qr")
    workflow.add_edge("generate_payment_qr", "schedule_payment_reminders")
    workflow.add_edge("schedule_payment_reminders", "send_qr_message")
    workflow.add_edge("send_qr_message", "send_success")

    workflow.add_edge("send_success", END)
    workflow.add_edge("send_cancelled", END)
    workflow.add_edge("send_unclear", END)

    return workflow.compile()
