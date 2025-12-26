"""Booking confirmation and creation node group.

Handles:
- Price calculation
- Showing booking summary
- Processing confirmation
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
from clients.frappe_yawlit import get_yawlit_client
from core.config import settings

logger = logging.getLogger(__name__)


async def calculate_price(state: BookingState) -> BookingState:
    """Calculate total price."""
    selected_service = state.get("selected_service", {})
    base_price = selected_service.get("base_price", 0)
    state["total_price"] = base_price
    logger.info(f"💰 Calculated price: ₹{base_price}")
    return state


async def send_confirmation(state: BookingState) -> BookingState:
    """Send booking confirmation for user approval, then pause for input."""
    result = await send_message_node(state, BookingConfirmationBuilder())

    # Pause and wait for user's confirmation
    result["should_proceed"] = False
    result["current_step"] = "awaiting_booking_confirmation"
    return result


async def extract_confirmation(state: BookingState) -> BookingState:
    """Extract YES/NO confirmation from user message."""
    user_message = state.get("user_message", "").lower()

    if "yes" in user_message or "confirm" in user_message or "ok" in user_message:
        state["confirmed"] = True
    elif "no" in user_message or "cancel" in user_message:
        state["confirmed"] = False
    else:
        state["confirmed"] = None  # Unclear

    logger.info(f"🔍 Confirmation extracted: {state.get('confirmed')}")
    return state


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
    """Create booking in Frappe using YawlitClient."""
    client = get_yawlit_client()

    def extract_booking_params(s):
        customer = s.get("customer", {})
        selected_service = s.get("selected_service", {})
        slot = s.get("slot", {})

        return {
            "customer_uuid": customer.get("customer_uuid"),
            "service_id": selected_service.get("product_id"),
            "vehicle_id": s.get("vehicle", {}).get("vehicle_id"),
            "slot_id": slot.get("slot_id"),
            "date": slot.get("date"),
            "address_id": customer.get("default_address_id"),
            "optional_addons": [],
            "special_instructions": ""
        }

    logger.info("📝 Creating booking...")
    return await call_frappe_node(
        state,
        client.booking_create.create_booking,
        "booking_response",
        state_extractor=extract_booking_params
    )


async def generate_payment_qr(state: BookingState) -> BookingState:
    """Generate UPI QR code for payment."""
    amount = state.get("total_price")
    booking_id = state.get("booking_response", {}).get("booking_id", "Unknown")

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
        booking_response = s.get("booking_response", {})
        message = booking_response.get("message", {})
        booking_id = message.get("booking_id", "Unknown")
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


def route_booking_entry(state: BookingState) -> str:
    """Route based on whether we're resuming or starting fresh."""
    current_step = state.get("current_step", "")
    has_price = state.get("total_price") is not None

    if current_step == "awaiting_booking_confirmation" and has_price:
        logger.info("🔀 Resuming booking confirmation - skipping price calc")
        return "extract_confirmation"
    else:
        logger.info("🔀 Starting fresh booking flow")
        return "calculate_price"


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
