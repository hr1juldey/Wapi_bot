"""Slot selection node group.

Handles:
- Fetching available slots from Frappe API
- Displaying slots to user
- Processing slot selection
- Error handling

Replaces 6 old nodes:
- fetch_slots
- format_slots
- send_slots
- await_slot_selection
- process_slot_selection
- handle_slot_selection_error
"""

import logging
from datetime import datetime, timedelta
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.selection.generic_handler import handle_selection, route_after_selection
from nodes.atomic.send_message import node as send_message_node
from nodes.atomic.transform import node as transform_node
from nodes.transformers.format_slot_options import FormatSlotOptions
from clients.frappe_yawlit import get_yawlit_client

logger = logging.getLogger(__name__)


async def fetch_slots(state: BookingState) -> BookingState:
    """Fetch available appointment slots from Frappe API.

    Queries slots for next 7 days based on selected service and vehicle type.
    """
    client = get_yawlit_client()

    # Get service ID from selected service
    selected_service = state.get("selected_service") or state.get("service")
    service_id = selected_service.get("name") if selected_service else None

    # Get vehicle type from vehicle
    vehicle = state.get("vehicle", {})
    vehicle_type = vehicle.get("vehicle_type") if vehicle else None

    if not service_id:
        logger.warning("⚠️ No service selected, cannot fetch slots")
        state["slot_options"] = []
        return state

    # Fetch slots for next 7 days
    all_slots = []
    today = datetime.now().date()

    for i in range(7):
        date = today + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")

        try:
            response = await client.slot_availability.get_available_slots_enhanced(
                service_id=service_id,
                date=date_str,
                vehicle_type=vehicle_type
            )

            # Extract slots from response
            slots = response.get("message", {}).get("slots", [])
            if not slots:
                slots = response.get("slots", [])
            if not slots and isinstance(response.get("message"), list):
                slots = response["message"]

            # Add date to each slot and mark as available
            for slot in slots:
                slot["date"] = date_str
                slot["available"] = slot.get("available", True)
                # Format time_slot if not present
                if "time_slot" not in slot:
                    start = slot.get("start_time", "")
                    end = slot.get("end_time", "")
                    if start and end:
                        slot["time_slot"] = f"{start} - {end}"

            all_slots.extend(slots)

        except Exception as e:
            logger.warning(f"⚠️ Failed to fetch slots for {date_str}: {e}")
            continue

    state["slot_options"] = all_slots
    logger.info(f"📅 Fetched {len(all_slots)} slot(s) from Frappe API")
    return state


async def format_and_send_slots(state: BookingState) -> BookingState:
    """Format and send slots to customer, then pause for user input."""
    # Format slots
    formatted = await transform_node(
        state,
        FormatSlotOptions(),
        "slot_options",
        "formatted_slots_message"
    )

    # Send formatted message
    def slots_message(s):
        return s.get("formatted_slots_message", "No slots available")

    result = await send_message_node(formatted, slots_message)

    # Pause and wait for user's slot selection
    result["should_proceed"] = False
    result["current_step"] = "awaiting_slot_selection"
    return result


async def process_slot_selection(state: BookingState) -> BookingState:
    """Process slot selection from user."""
    return await handle_selection(
        state,
        selection_type="slot",
        options_key="slot_options",
        selected_key="slot"
    )


async def send_slot_error(state: BookingState) -> BookingState:
    """Send error message for invalid slot selection."""
    error_msg = state.get("selection_error", "Invalid selection. Please try again.")
    result = await send_message_node(state, lambda s: error_msg)
    result["should_proceed"] = False  # Stop and wait for next user message
    result["current_step"] = "awaiting_slot_selection"  # Resume here on next message
    return result


def route_slot_entry(state: BookingState) -> str:
    """Route based on whether we're resuming or starting fresh."""
    current_step = state.get("current_step", "")
    has_slots = bool(state.get("slot_options"))

    if current_step == "awaiting_slot_selection" and has_slots:
        logger.info("🔀 Resuming slot selection - skipping fetch")
        return "process_selection"
    else:
        logger.info("🔀 Starting fresh slot fetch")
        return "fetch_slots"


def create_slot_group() -> StateGraph:
    """Create slot selection node group."""
    workflow = StateGraph(BookingState)

    # Add nodes
    workflow.add_node("entry", lambda s: s)  # Pass-through entry
    workflow.add_node("fetch_slots", fetch_slots)
    workflow.add_node("show_slots", format_and_send_slots)
    workflow.add_node("process_selection", process_slot_selection)
    workflow.add_node("send_error", send_slot_error)

    # Start at entry for routing
    workflow.set_entry_point("entry")

    # Route based on resume state
    workflow.add_conditional_edges(
        "entry",
        route_slot_entry,
        {
            "fetch_slots": "fetch_slots",
            "process_selection": "process_selection"
        }
    )

    workflow.add_edge("fetch_slots", "show_slots")
    # After showing slots, END and wait for user input (pause)
    workflow.add_edge("show_slots", END)

    workflow.add_conditional_edges(
        "process_selection",
        route_after_selection,
        {
            "selection_error": "send_error",
            "selection_success": END
        }
    )

    # Error path: send error and END (don't loop!)
    workflow.add_edge("send_error", END)

    return workflow.compile()
