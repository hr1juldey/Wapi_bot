"""Vehicle selection node group - display options, process selection, handle errors."""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.selection.generic_handler import handle_selection, route_after_selection
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.vehicle_options import VehicleOptionsBuilder
from nodes.error_handling.selection_error_handler import handle_selection_error

logger = logging.getLogger(__name__)


async def show_vehicle_options(state: BookingState) -> BookingState:
    """Display vehicle options to user, then pause for input."""
    result = await send_message_node(state, VehicleOptionsBuilder())

    # Pause and wait for user's vehicle selection
    result["should_proceed"] = False
    result["current_step"] = "awaiting_vehicle_selection"
    return result


async def process_vehicle_selection(state: BookingState) -> BookingState:
    """Process vehicle selection from user."""
    result = await handle_selection(
        state,
        selection_type="vehicle",
        options_key="vehicle_options",
        selected_key="vehicle"
    )
    # Clear current_step to indicate we're moving to the next step (service selection)
    if result.get("vehicle"):
        result["current_step"] = ""
        result["should_proceed"] = True  # Continue to next step
    return result


async def send_vehicle_error(state: BookingState) -> BookingState:
    """Send error message for invalid vehicle selection."""
    return await handle_selection_error(
        state,
        awaiting_step="awaiting_vehicle_selection"
    )


def route_vehicle_entry(state: BookingState) -> str:
    """Route based on whether we're resuming or starting fresh."""
    current_step = state.get("current_step", "")
    has_options = bool(state.get("vehicle_options"))

    # If resuming vehicle selection, go directly to process
    if current_step == "awaiting_vehicle_selection" and has_options:
        logger.info("🔀 Resuming vehicle selection - skipping show")
        return "process_selection"

    # Check if vehicle already selected (skip entire group)
    if state.get("vehicle_selected", False):
        logger.info("🔀 Vehicle already selected - skipping")
        return "skip"

    # No vehicle options means skip
    vehicle_options = state.get("vehicle_options", [])
    if len(vehicle_options) == 0:
        logger.info("🔀 No vehicle options - skipping")
        return "skip"

    # Need to show options
    logger.info("🔀 Showing vehicle options")
    return "show_options"


async def skip_vehicle_selection(state: BookingState) -> BookingState:
    """Skip vehicle selection (already done)."""
    state["should_proceed"] = True
    return state


def create_vehicle_group() -> StateGraph:
    """Create vehicle selection workflow."""
    workflow = StateGraph(BookingState)
    workflow.add_node("entry", lambda s: s)
    workflow.add_node("skip_selection", skip_vehicle_selection)
    workflow.add_node("show_options", show_vehicle_options)
    workflow.add_node("process_selection", process_vehicle_selection)
    workflow.add_node("send_error", send_vehicle_error)
    workflow.set_entry_point("entry")
    workflow.add_conditional_edges("entry", route_vehicle_entry,
        {"skip": "skip_selection", "show_options": "show_options", "process_selection": "process_selection"})
    workflow.add_edge("skip_selection", END)
    workflow.add_edge("show_options", END)
    workflow.add_conditional_edges("process_selection", route_after_selection,
        {"selection_error": "send_error", "selection_success": END})
    workflow.add_edge("send_error", END)
    return workflow.compile()
