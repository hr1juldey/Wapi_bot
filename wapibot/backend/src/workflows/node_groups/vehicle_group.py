"""Vehicle selection node group.

Handles:
- Displaying vehicle options (if multiple)
- Processing user selection
- Error handling for invalid selections

Replaces 6 old nodes:
- send_vehicle_options
- await_vehicle_selection
- process_vehicle_selection
- handle_vehicle_selection_error
- validate_vehicle_selection
- route_vehicle_selection
"""

import logging
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.selection.generic_handler import handle_selection, route_after_selection
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.vehicle_options import VehicleOptionsBuilder

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
    error_msg = state.get("selection_error", "Invalid selection. Please try again.")
    result = await send_message_node(state, lambda s: error_msg)
    result["should_proceed"] = False  # Stop and wait for next user message
    result["current_step"] = "awaiting_vehicle_selection"  # Resume here on next message
    return result


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
    """Create vehicle selection node group.

    Inputs:
    - state["vehicle_options"]: List of vehicles

    Outputs:
    - state["vehicle"]: Selected vehicle
    - state["vehicle_selected"]: True when done
    """
    workflow = StateGraph(BookingState)

    # Add nodes
    workflow.add_node("entry", lambda s: s)  # Pass-through entry
    workflow.add_node("skip_selection", skip_vehicle_selection)
    workflow.add_node("show_options", show_vehicle_options)
    workflow.add_node("process_selection", process_vehicle_selection)
    workflow.add_node("send_error", send_vehicle_error)

    # Start at entry for routing
    workflow.set_entry_point("entry")

    # Route based on resume state
    workflow.add_conditional_edges(
        "entry",
        route_vehicle_entry,
        {
            "skip": "skip_selection",
            "show_options": "show_options",
            "process_selection": "process_selection"
        }
    )

    workflow.add_edge("skip_selection", END)
    # After showing options, END and wait for user input (pause)
    workflow.add_edge("show_options", END)

    # After processing selection
    workflow.add_conditional_edges(
        "process_selection",
        route_after_selection,
        {
            "selection_error": "send_error",  # Invalid selection
            "selection_success": END  # Valid selection, done
        }
    )

    # Error path: send error and END (don't loop!)
    workflow.add_edge("send_error", END)

    return workflow.compile()
