"""Utilities collection node group.

Handles:
- Asking about electricity and water availability (via message builder)
- Extracting yes/no responses for both utilities
- Validating that both fields are set
"""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.utilities_selection import UtilitiesSelectionBuilder

logger = logging.getLogger(__name__)


async def ask_utilities(state: BookingState) -> BookingState:
    """Send utilities question using message builder."""
    result = await send_message_node(state, UtilitiesSelectionBuilder())

    # Pause and wait for user's response
    result["should_proceed"] = False
    result["current_step"] = "awaiting_utilities"
    return result


async def extract_utilities(state: BookingState) -> BookingState:
    """Extract yes/no for electricity and water from user message."""
    user_message = state.get("user_message", "").strip().lower()

    # Parse yes/no responses
    words = user_message.split()
    yes_no_words = []

    for word in words:
        if "yes" in word or "yeah" in word or "y" == word:
            yes_no_words.append(1)
        elif "no" in word or "nah" in word or "n" == word:
            yes_no_words.append(0)

    # Validate we got exactly 2 responses
    if len(yes_no_words) >= 2:
        state["electricity_provided"] = yes_no_words[0]
        state["water_provided"] = yes_no_words[1]
        logger.info(f"⚡ Electricity: {yes_no_words[0]}, 💧 Water: {yes_no_words[1]}")
    elif len(yes_no_words) == 1:
        # User provided only one answer - assume both are the same
        state["electricity_provided"] = yes_no_words[0]
        state["water_provided"] = yes_no_words[0]
        logger.info(f"⚡💧 Both utilities: {yes_no_words[0]} (inferred from single answer)")
    else:
        # Could not parse
        logger.warning(f"Could not parse utilities response: {user_message}")

    return state


async def validate_utilities(state: BookingState) -> BookingState:
    """Validate that both utility fields are set."""
    electricity = state.get("electricity_provided")
    water = state.get("water_provided")

    if electricity is not None and water is not None:
        logger.info("✅ Utilities validated")
    else:
        logger.warning("⚠️ Utilities validation failed")

    return state


async def send_invalid_utilities(state: BookingState) -> BookingState:
    """Send message for invalid utilities response."""

    def invalid_message(s):
        return """Please reply with "Yes" or "No" for both electricity and water.

Examples:
• "Yes Yes" - Both available
• "Yes No" - Only electricity
• "No Yes" - Only water
• "No No" - Neither available
"""

    result = await send_message_node(state, invalid_message)
    result["should_proceed"] = False
    result["current_step"] = "awaiting_utilities"
    return result


def route_utilities_validation(state: BookingState) -> str:
    """Route based on utilities validation."""
    electricity = state.get("electricity_provided")
    water = state.get("water_provided")

    if electricity is not None and water is not None:
        return "valid"
    else:
        return "invalid"


def route_utilities_entry(state: BookingState) -> str:
    """Route based on whether we're resuming or starting fresh."""
    current_step = state.get("current_step", "")
    electricity = state.get("electricity_provided")
    water = state.get("water_provided")

    if current_step == "awaiting_utilities" and (electricity is None or water is None):
        logger.info("🔀 Resuming utilities collection - extracting response")
        return "extract_utilities"
    else:
        logger.info("🔀 Starting fresh utilities collection")
        return "ask_utilities"


def create_utilities_group() -> StateGraph:
    """Create utilities collection node group."""
    workflow = StateGraph(BookingState)

    # Add nodes
    workflow.add_node("entry", lambda s: s)  # Pass-through entry
    workflow.add_node("ask_utilities", ask_utilities)
    workflow.add_node("extract_utilities", extract_utilities)
    workflow.add_node("validate_utilities", validate_utilities)
    workflow.add_node("send_invalid_utilities", send_invalid_utilities)

    # Start at entry for routing
    workflow.set_entry_point("entry")

    # Route based on resume state
    workflow.add_conditional_edges(
        "entry",
        route_utilities_entry,
        {
            "ask_utilities": "ask_utilities",
            "extract_utilities": "extract_utilities"
        }
    )

    # After asking, END and wait for user input
    workflow.add_edge("ask_utilities", END)

    # After extracting, validate
    workflow.add_edge("extract_utilities", "validate_utilities")

    # Route based on validation
    workflow.add_conditional_edges(
        "validate_utilities",
        route_utilities_validation,
        {
            "valid": END,  # Valid response, proceed
            "invalid": "send_invalid_utilities"
        }
    )

    # After invalid message, END and wait for retry
    workflow.add_edge("send_invalid_utilities", END)

    return workflow.compile()
