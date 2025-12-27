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
    """Calculate real price using Frappe API (handles addons, discounts, taxes)."""
    selected_service = state.get("selected_service", {})
    base_price = selected_service.get("base_price", 0)

    try:
        client = get_yawlit_client()

        def extract_price_params(s):
            # Wrap in price_data because calculate_price(price_data: Dict) expects it
            addon_ids = s.get("addon_ids", [])
            price_params = {
                "price_data": {
                    "product_id": selected_service.get("name"),
                    "optional_addons": addon_ids,
                    "electricity_provided": s.get("electricity_provided", 1),
                    "water_provided": s.get("water_provided", 1)
                }
            }
            logger.info(f"💰 Price params: product={selected_service.get('name')}, addons={addon_ids}, elec={s.get('electricity_provided', 1)}, water={s.get('water_provided', 1)}")
            return price_params

        logger.info("💰 Calling calculate_booking_price API...")
        result = await call_frappe_node(
            state,
            client.booking_create.calculate_price,
            "price_breakdown",
            state_extractor=extract_price_params
        )

        # Extract total_price from API response (unwrap message structure)
        price_api_response = result.get("price_breakdown", {})
        price_breakdown = price_api_response.get("message", {})
        total_price = price_breakdown.get("total_amount")  # API uses total_amount, not total_price

        if total_price and total_price > 0:
            result["total_price"] = total_price
            # Try both field names (addon_price and addons_total)
            addon_amount = price_breakdown.get('addon_price', 0) or price_breakdown.get('addons_total', 0)
            logger.info(f"💰 API price: ₹{total_price} (base: {price_breakdown.get('base_price', 0)}, addons: {addon_amount}, tax: {price_breakdown.get('tax', 0)})")
            logger.info(f"💰 Full price breakdown: {price_breakdown}")
            return result
        else:
            # API returned invalid price, use fallback
            raise ValueError("Invalid price from API")

    except Exception as e:
        # Fallback to base price
        logger.warning(f"Price calculation failed: {e}. Using base_price: ₹{base_price}")
        state["total_price"] = base_price
        state["price_breakdown"] = {
            "base_price": base_price,
            "addon_price": 0,
            "discount": 0,
            "tax": 0,
            "total_price": base_price
        }
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
    """Create booking using phone-based API (no session required)."""
    client = get_yawlit_client()

    def extract_booking_params(s):
        customer = s.get("customer", {})
        selected_service = s.get("selected_service", {})
        slot = s.get("slot", {})

        # Extract and normalize phone from conversation_id
        phone = s.get("conversation_id", "")
        # Remove country code (91) if present
        if phone.startswith("91") and len(phone) == 12:
            phone = phone[2:]  # Extract last 10 digits
        elif len(phone) == 10:
            phone = phone  # Already in correct format
        else:
            logger.warning(f"Unexpected phone format: {phone}")
            phone = phone[-10:]  # Fallback: take last 10 digits

        logger.info(f"📱 Phone normalized: {s.get('conversation_id')} → {phone}")

        # Extract booking data fields
        product_id = selected_service.get("name")
        booking_date = slot.get("date")
        slot_id = slot.get("name")  # slot.name is the actual slot ID (e.g., "SLOT-1568")
        vehicle_id = s.get("vehicle", {}).get("vehicle_id")
        address_id = s.get("selected_address_id") or customer.get("default_address_id")

        # Validate required fields
        missing_fields = []
        if not product_id:
            missing_fields.append("product_id")
        if not booking_date:
            missing_fields.append("booking_date")
        if not slot_id:
            missing_fields.append("slot_id")
        if not vehicle_id:
            missing_fields.append("vehicle_id")
        if not address_id:
            missing_fields.append("address_id")

        if missing_fields:
            logger.error(f"❌ Missing required fields: {', '.join(missing_fields)}")
            logger.error(f"   selected_service keys: {list(selected_service.keys())}")
            logger.error(f"   slot keys: {list(slot.keys())}")
            logger.error(f"   vehicle keys: {list(s.get('vehicle', {}).keys())}")
            logger.error(f"   customer keys: {list(customer.keys())}")

        # Log booking data for debugging
        addon_ids = s.get("addon_ids", [])
        logger.info(f"📋 Booking data: product_id={product_id}, date={booking_date}, slot_id={slot_id}, vehicle_id={vehicle_id}, address_id={address_id}, addon_ids={addon_ids}")

        # Return phone_number and booking_data separately (method signature requirement)
        return {
            "phone_number": phone,
            "booking_data": {
                "product_id": product_id,
                "booking_date": booking_date,
                "slot_id": slot_id,
                "vehicle_id": vehicle_id,
                "address_id": address_id,
                "electricity_provided": s.get("electricity_provided", 1),
                "water_provided": s.get("water_provided", 1),
                "addon_ids": s.get("addon_ids", []),
                "payment_mode": "Pay Now"
            }
        }

    logger.info("📝 Creating booking via create_booking_by_phone...")
    result = await call_frappe_node(
        state,
        client.booking_create.create_booking_by_phone,
        "booking_api_response",
        state_extractor=extract_booking_params
    )

    # Extract booking data from nested response structure
    api_response = result.get("booking_api_response", {})
    message = api_response.get("message", {})

    # Preserve state and merge in new booking data
    state["booking_response"] = message
    state["booking_id"] = message.get("booking_id", "Unknown")
    state["booking_data"] = message.get("booking_data", {})

    logger.info(f"✅ Booking created: {state.get('booking_id')}")
    logger.info(f"📋 Booking ID in state: {state.get('booking_id')}")
    logger.info(f"📋 State keys: {list(state.keys())}")
    return state


async def generate_payment_qr(state: BookingState) -> BookingState:
    """Generate UPI QR code for payment."""
    amount = state.get("total_price")
    booking_id = state.get("booking_id", "Unknown")
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
