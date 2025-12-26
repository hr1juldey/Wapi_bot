"""Generic selection handler for ANY list-based user selection.

Handles:
- Vehicle selection (from vehicle_options)
- Service selection (from service_options)
- Slot selection (from slot_options)
- Addon selection (from addon_options)

Replaces 3 duplicate nodes:
- handle_vehicle_selection_error
- handle_service_selection_error
- handle_slot_selection_error
"""

import logging
from typing import List, Dict, Any, Optional
from workflows.shared.state import BookingState

logger = logging.getLogger(__name__)


async def handle_selection(
    state: BookingState,
    selection_type: str,      # "vehicle" | "service" | "slot" | "addon"
    options_key: str,         # "vehicle_options" | "service_options" | ...
    selected_key: str,        # "vehicle" | "service" | "slot" | "addons"
    user_input_key: str = "user_message"
) -> BookingState:
    """Process user selection from a list of options.

    Args:
        selection_type: Human-readable type for error messages
        options_key: State key containing options list
        selected_key: State key to store selected item
        user_input_key: State key containing user input

    Returns:
        Updated state with selection or error message
    """
    user_input = state.get(user_input_key, "").strip()
    options = state.get(options_key, [])

    logger.info(f"Processing {selection_type} selection: '{user_input}' from {len(options)} options")

    # Validate input is numeric
    try:
        selection_index = int(user_input) - 1  # Convert to 0-based
    except ValueError:
        error_msg = f"Please reply with a number from 1 to {len(options)}"
        logger.warning(f"⚠️ Invalid input: not a number")
        state["selection_error"] = error_msg
        return state

    # Validate index in range
    if selection_index < 0 or selection_index >= len(options):
        error_msg = f"Please reply with a number from 1 to {len(options)}"
        logger.warning(f"⚠️ Invalid input: out of range ({selection_index + 1})")
        state["selection_error"] = error_msg
        return state

    # Store selection
    selected_item = options[selection_index]
    state[selected_key] = selected_item
    state[f"{selected_key}_selected"] = True

    # Clear error and options
    state["selection_error"] = None
    state[options_key] = []

    logger.info(f"✅ {selection_type.capitalize()} selected: {selected_item}")

    return state


async def route_after_selection(state: BookingState) -> str:
    """Route after selection attempt.

    Returns:
        - "selection_error": Invalid input, re-prompt
        - "selection_success": Valid selection made
    """
    has_error = state.get("selection_error") is not None
    route = "selection_error" if has_error else "selection_success"
    logger.info(f"🔀 Route after selection: {route}")
    return route
