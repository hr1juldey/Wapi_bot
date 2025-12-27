"""Addon selection node group.

Handles:
- Fetching available addons for selected service
- Showing addon options with prices
- Extracting user's addon selection (supports multiple or skip)
- Validating addon selection
"""

import logging
import re
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from nodes.atomic.call_frappe import node as call_frappe_node
from clients.frappe_yawlit import get_yawlit_client

logger = logging.getLogger(__name__)


async def fetch_addons(state: BookingState) -> BookingState:
    """Fetch available addons for selected service from Frappe API."""
    client = get_yawlit_client()

    def extract_service_id(s):
        selected_service = s.get("selected_service", {})
        return {"service_id": selected_service.get("product_id")}

    logger.info("➕ Fetching optional addons from API...")
    result = await call_frappe_node(
        state,
        client.service_catalog.get_optional_addons,
        "available_addons",
        state_extractor=extract_service_id
    )

    # Check if any addons available
    addons = result.get("available_addons", [])
    if not addons:
        logger.info("No addons available for this service - auto-skipping")
        result["skipped_addons"] = True
        result["addon_selection_complete"] = True
        result["addon_ids"] = []

    return result


async def show_addon_options(state: BookingState) -> BookingState:
    """Show addon options with prices for user to choose from."""

    def build_addon_message(s):
        addons = s.get("available_addons", [])
        service_name = s.get("selected_service", {}).get("service_name", "service")
        customer_name = s.get("customer", {}).get("first_name", "there")

        # Build addon list
        addon_list = []
        for idx, addon in enumerate(addons, 1):
            addon_name = addon.get("addon_name", "")
            price = addon.get("price", 0)
            description = addon.get("description", "")

            addon_text = f"{idx}. *{addon_name}* - ₹{price}"
            if description:
                addon_text += f"\n   {description}"

            addon_list.append(addon_text)

        addons_text = "\n\n".join(addon_list)

        return f"""Great choice, {customer_name}! 🎉

Your selected service: *{service_name}*

Would you like to add any extras?

*Available Add-ons:*

{addons_text}

*To select:*
• Reply with numbers (e.g., "1 3" for addons 1 and 3)
• Reply "None" or "Skip" if you don't want any addons"""

    result = await send_message_node(state, build_addon_message)

    # Pause and wait for user's selection
    result["should_proceed"] = False
    result["current_step"] = "awaiting_addon_selection"
    return result


async def extract_addon_selection(state: BookingState) -> BookingState:
    """Extract addon selection from user message."""
    user_message = state.get("user_message", "").strip().lower()
    available_addons = state.get("available_addons", [])

    # Check for skip keywords
    if any(keyword in user_message for keyword in ["none", "skip", "no", "nah"]):
        state["skipped_addons"] = True
        state["addon_selection_complete"] = True
        state["addon_ids"] = []
        state["selected_addons"] = []
        logger.info("➕ User skipped addon selection")
        return state

    # Try to parse numbers
    selected_indices = []
    selected_addons = []
    addon_ids = []

    numbers = re.findall(r'\d+', user_message)
    for num in numbers:
        try:
            idx = int(num)
            if 1 <= idx <= len(available_addons):
                if idx not in selected_indices:  # Avoid duplicates
                    selected_indices.append(idx)
                    addon = available_addons[idx - 1]
                    selected_addons.append(addon)
                    addon_ids.append(addon.get("name"))  # Use addon document name as ID
        except ValueError:
            continue

    if selected_indices:
        state["selected_addons"] = selected_addons
        state["addon_ids"] = addon_ids
        state["addon_selection_complete"] = True
        state["skipped_addons"] = False
        logger.info(f"➕ Addons selected: {addon_ids} (options {selected_indices})")
    else:
        state["addon_selection_complete"] = False
        logger.warning(f"Could not parse addon selection: {user_message}")

    return state


async def validate_addon_selection(state: BookingState) -> BookingState:
    """Validate that addon selection is complete."""
    if not state.get("addon_selection_complete"):
        logger.warning("Addon selection validation failed")

    return state


async def send_invalid_addon_selection(state: BookingState) -> BookingState:
    """Send message for invalid addon selection."""

    def invalid_message(s):
        available_addons = s.get("available_addons", [])
        return f"""Please reply with valid numbers between 1 and {len(available_addons)}, or "Skip" if you don't want any addons.

Examples:
• "1" - Select addon 1
• "1 3" - Select addons 1 and 3
• "Skip" - No addons"""

    result = await send_message_node(state, invalid_message)
    result["should_proceed"] = False
    result["current_step"] = "awaiting_addon_selection"
    return result


def route_addon_availability(state: BookingState) -> str:
    """Route based on whether addons are available."""
    available_addons = state.get("available_addons", [])
    if not available_addons:
        return "no_addons"  # Skip to END
    else:
        return "show_options"


def route_addon_validation(state: BookingState) -> str:
    """Route based on addon selection validation."""
    if state.get("addon_selection_complete"):
        return "valid"
    else:
        return "invalid"


def route_addon_entry(state: BookingState) -> str:
    """Route based on whether we're resuming or starting fresh."""
    current_step = state.get("current_step", "")
    addon_complete = state.get("addon_selection_complete", False)

    if current_step == "awaiting_addon_selection" and not addon_complete:
        logger.info("🔀 Resuming addon selection - extracting choice")
        return "extract_selection"
    else:
        logger.info("🔀 Starting fresh addon selection")
        return "fetch_addons"


def create_addon_group() -> StateGraph:
    """Create addon selection node group."""
    workflow = StateGraph(BookingState)

    # Add nodes
    workflow.add_node("entry", lambda s: s)  # Pass-through entry
    workflow.add_node("fetch_addons", fetch_addons)
    workflow.add_node("show_addon_options", show_addon_options)
    workflow.add_node("extract_addon_selection", extract_addon_selection)
    workflow.add_node("validate_addon_selection", validate_addon_selection)
    workflow.add_node("send_invalid_addon_selection", send_invalid_addon_selection)

    # Start at entry for routing
    workflow.set_entry_point("entry")

    # Route based on resume state
    workflow.add_conditional_edges(
        "entry",
        route_addon_entry,
        {
            "fetch_addons": "fetch_addons",
            "extract_selection": "extract_addon_selection"
        }
    )

    # Route based on addon availability
    workflow.add_conditional_edges(
        "fetch_addons",
        route_addon_availability,
        {
            "no_addons": END,  # No addons, skip to end
            "show_options": "show_addon_options"
        }
    )

    # After showing options, END and wait for user input
    workflow.add_edge("show_addon_options", END)

    # After extracting selection, validate it
    workflow.add_edge("extract_addon_selection", "validate_addon_selection")

    # Route based on validation
    workflow.add_conditional_edges(
        "validate_addon_selection",
        route_addon_validation,
        {
            "valid": END,  # Valid selection, proceed
            "invalid": "send_invalid_addon_selection"
        }
    )

    # After invalid message, END and wait for retry
    workflow.add_edge("send_invalid_addon_selection", END)

    return workflow.compile()
