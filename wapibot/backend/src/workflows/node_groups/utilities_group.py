"""Utilities collection - ask, extract, validate electricity/water availability."""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.utilities_selection import UtilitiesSelectionBuilder
from nodes.routing.resume_router import create_resume_router
from nodes.error_handling.selection_error_handler import handle_selection_error

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
    def error_msg(s):
        return 'Please reply "Yes" or "No" for both.\nE.g., "Yes Yes", "Yes No", "No Yes", "No No"'
    return await handle_selection_error(state, awaiting_step="awaiting_utilities", error_message_builder=error_msg)


def route_utilities_validation(state: BookingState) -> str:
    """Route based on utilities validation."""
    electricity = state.get("electricity_provided")
    water = state.get("water_provided")

    if electricity is not None and water is not None:
        return "valid"
    else:
        return "invalid"


# Create resume router for entry point
route_utilities_entry = create_resume_router(
    awaiting_step="awaiting_utilities",
    resume_node="extract_utilities",
    fresh_node="ask_utilities",
    readiness_check=lambda s: s.get("electricity_provided") is None or s.get("water_provided") is None,
    router_name="utilities_entry"
)


def create_utilities_group() -> StateGraph:
    """Create utilities collection workflow."""
    workflow = StateGraph(BookingState)
    workflow.add_node("entry", lambda s: s)
    workflow.add_node("ask_utilities", ask_utilities)
    workflow.add_node("extract_utilities", extract_utilities)
    workflow.add_node("validate_utilities", validate_utilities)
    workflow.add_node("send_invalid_utilities", send_invalid_utilities)
    workflow.set_entry_point("entry")
    workflow.add_conditional_edges("entry", route_utilities_entry,
        {"ask_utilities": "ask_utilities", "extract_utilities": "extract_utilities"})
    workflow.add_edge("ask_utilities", END)
    workflow.add_edge("extract_utilities", "validate_utilities")
    workflow.add_conditional_edges("validate_utilities", route_utilities_validation,
        {"valid": END, "invalid": "send_invalid_utilities"})
    workflow.add_edge("send_invalid_utilities", END)
    return workflow.compile()
