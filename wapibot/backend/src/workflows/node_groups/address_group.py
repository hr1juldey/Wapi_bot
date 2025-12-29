"""Address selection - check count, auto-select, show options, extract, validate."""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.address_selection import AddressSelectionBuilder
from nodes.routing.resume_router import create_resume_router
from nodes.error_handling.selection_error_handler import handle_selection_error

logger = logging.getLogger(__name__)


async def check_address_count(state: BookingState) -> BookingState:
    """Check how many addresses customer has."""
    addresses = state.get("addresses", [])
    address_count = len(addresses)

    logger.info(f"🏠 Customer has {address_count} address(es)")

    if address_count == 0:
        logger.error("No addresses found for customer")
        state["errors"] = state.get("errors", []) + ["No addresses available"]
    elif address_count == 1:
        # Auto-select single address
        address = addresses[0]
        state["selected_address_id"] = address.get("name")
        state["address_selected"] = True
        logger.info(f"🏠 Auto-selected single address: {address.get('name')}")

    return state


async def show_address_options(state: BookingState) -> BookingState:
    """Show address options using message builder."""
    result = await send_message_node(state, AddressSelectionBuilder())

    # Pause and wait for user's selection
    result["should_proceed"] = False
    result["current_step"] = "awaiting_address_selection"
    return result


async def extract_address_selection(state: BookingState) -> BookingState:
    """Extract address selection from user message."""
    user_message = state.get("user_message", "").strip()
    addresses = state.get("addresses", [])

    # Try to parse as number
    try:
        selection = int(user_message)
        if 1 <= selection <= len(addresses):
            selected_address = addresses[selection - 1]
            state["selected_address_id"] = selected_address.get("name")
            state["address_selected"] = True
            logger.info(f"🏠 Address selected: {selected_address.get('name')} (option {selection})")
        else:
            state["address_selected"] = False
            logger.warning(f"Invalid selection: {selection} (out of range 1-{len(addresses)})")
    except ValueError:
        # Not a number, try fuzzy matching
        state["address_selected"] = False
        logger.warning(f"Could not parse address selection: {user_message}")

    return state


async def validate_address_selection(state: BookingState) -> BookingState:
    """Validate that a valid address was selected."""
    if not state.get("address_selected"):
        logger.warning("Address selection validation failed")

    return state


async def send_invalid_address_selection(state: BookingState) -> BookingState:
    """Send message for invalid address selection."""
    def error_msg(s):
        return f"Please reply with a valid number between 1 and {len(s.get('addresses', []))}."
    return await handle_selection_error(state, awaiting_step="awaiting_address_selection", error_message_builder=error_msg)


def route_address_count(state: BookingState) -> str:
    """Route based on number of addresses."""
    addresses = state.get("addresses", [])
    address_count = len(addresses)

    if address_count == 0:
        return "error"
    elif address_count == 1:
        return "auto_selected"  # Skip to END
    else:
        return "show_options"


def route_address_validation(state: BookingState) -> str:
    """Route based on address selection validation."""
    if state.get("address_selected"):
        return "valid"
    else:
        return "invalid"


# Create resume router for entry point
route_address_entry = create_resume_router(
    awaiting_step="awaiting_address_selection",
    resume_node="extract_selection",
    fresh_node="check_count",
    readiness_check=lambda s: not s.get("address_selected", False),
    router_name="address_entry"
)


def create_address_group() -> StateGraph:
    """Create address selection workflow."""
    workflow = StateGraph(BookingState)
    workflow.add_node("entry", lambda s: s)
    workflow.add_node("check_address_count", check_address_count)
    workflow.add_node("show_address_options", show_address_options)
    workflow.add_node("extract_address_selection", extract_address_selection)
    workflow.add_node("validate_address_selection", validate_address_selection)
    workflow.add_node("send_invalid_address_selection", send_invalid_address_selection)
    workflow.set_entry_point("entry")
    workflow.add_conditional_edges("entry", route_address_entry,
        {"check_count": "check_address_count", "extract_selection": "extract_address_selection"})
    workflow.add_conditional_edges("check_address_count", route_address_count,
        {"auto_selected": END, "show_options": "show_address_options", "error": END})
    workflow.add_edge("show_address_options", END)
    workflow.add_edge("extract_address_selection", "validate_address_selection")
    workflow.add_conditional_edges("validate_address_selection", route_address_validation,
        {"valid": END, "invalid": "send_invalid_address_selection"})
    workflow.add_edge("send_invalid_address_selection", END)
    return workflow.compile()
