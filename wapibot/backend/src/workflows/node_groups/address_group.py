"""Address selection node group.

Handles:
- Checking if customer has multiple addresses
- Auto-selecting if only one address
- Showing address options if multiple
- Extracting and validating user's address selection
"""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node

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
    """Show address options for user to choose from."""

    def build_address_message(s):
        addresses = s.get("addresses", [])
        customer_name = s.get("customer", {}).get("first_name", "there")

        # Build address list
        address_list = []
        for idx, addr in enumerate(addresses, 1):
            line1 = addr.get("address_line1", "")
            line2 = addr.get("address_line2", "")
            city = addr.get("city", "")
            pincode = addr.get("pincode", "")

            # Format address nicely
            full_addr = line1
            if line2:
                full_addr += f", {line2}"
            full_addr += f"\n   {city} - {pincode}"

            address_list.append(f"{idx}. {full_addr}")

        addresses_text = "\n\n".join(address_list)

        return f"""Hi {customer_name}! 👋

Where would you like us to service your vehicle?

Your saved addresses:

{addresses_text}

Please reply with the number of your preferred location (e.g., "1" or "2")."""

    result = await send_message_node(state, build_address_message)

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

    def invalid_message(s):
        addresses = s.get("addresses", [])
        return f"Please reply with a valid number between 1 and {len(addresses)}."

    result = await send_message_node(state, invalid_message)
    result["should_proceed"] = False
    result["current_step"] = "awaiting_address_selection"
    return result


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


def route_address_entry(state: BookingState) -> str:
    """Route based on whether we're resuming or starting fresh."""
    current_step = state.get("current_step", "")
    address_selected = state.get("address_selected", False)

    if current_step == "awaiting_address_selection" and not address_selected:
        logger.info("🔀 Resuming address selection - extracting choice")
        return "extract_selection"
    else:
        logger.info("🔀 Starting fresh address selection")
        return "check_count"


def create_address_group() -> StateGraph:
    """Create address selection node group."""
    workflow = StateGraph(BookingState)

    # Add nodes
    workflow.add_node("entry", lambda s: s)  # Pass-through entry
    workflow.add_node("check_address_count", check_address_count)
    workflow.add_node("show_address_options", show_address_options)
    workflow.add_node("extract_address_selection", extract_address_selection)
    workflow.add_node("validate_address_selection", validate_address_selection)
    workflow.add_node("send_invalid_address_selection", send_invalid_address_selection)

    # Start at entry for routing
    workflow.set_entry_point("entry")

    # Route based on resume state
    workflow.add_conditional_edges(
        "entry",
        route_address_entry,
        {
            "check_count": "check_address_count",
            "extract_selection": "extract_address_selection"
        }
    )

    # Route based on address count
    workflow.add_conditional_edges(
        "check_address_count",
        route_address_count,
        {
            "auto_selected": END,  # Single address, skip to end
            "show_options": "show_address_options",
            "error": END  # No addresses, should error upstream
        }
    )

    # After showing options, END and wait for user input
    workflow.add_edge("show_address_options", END)

    # After extracting selection, validate it
    workflow.add_edge("extract_address_selection", "validate_address_selection")

    # Route based on validation
    workflow.add_conditional_edges(
        "validate_address_selection",
        route_address_validation,
        {
            "valid": END,  # Valid selection, proceed
            "invalid": "send_invalid_address_selection"
        }
    )

    # After invalid message, END and wait for retry
    workflow.add_edge("send_invalid_address_selection", END)

    return workflow.compile()
