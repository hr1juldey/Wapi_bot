"""Selection error handler - generic error messaging for selection workflows.

SOLID Principles:
- Single Responsibility: ONLY handles selection validation errors
- Open/Closed: Extensible via error message builders
- Dependency Inversion: Accepts callable message builders

DRY Principle:
- ONE implementation for ALL selection error handling
- Eliminates ~90 lines of duplicated error handler code across 6 node groups

Blender Architecture:
- Generic error handler (like Blender's error nodes)
- Configurable via message builder, not hardcoding
"""

import logging
from typing import Callable, Optional
from workflows.shared.state import BookingState
from nodes.atomic.send_message import node as send_message_node

logger = logging.getLogger(__name__)

# Type alias for error message builders
ErrorMessageBuilder = Callable[[BookingState], str]


async def handle_selection_error(
    state: BookingState,
    awaiting_step: str,
    error_message_builder: Optional[ErrorMessageBuilder] = None,
    default_error: str = "Invalid selection. Please try again."
) -> BookingState:
    """Generic selection error handler for node groups.

    Sends error message and pauses workflow for user retry.

    Args:
        state: Current booking state
        awaiting_step: Step name to resume on (e.g., "awaiting_service_selection")
        error_message_builder: Optional function to build error message from state
                              If None, uses state.get("selection_error") or default_error
        default_error: Default error message if no builder and no selection_error in state

    Returns:
        Updated state with error message sent and workflow paused

    Examples:
        # Using state's selection_error field
        result = await handle_selection_error(
            state,
            awaiting_step="awaiting_service_selection"
        )

        # Using custom error message builder
        def build_error(s):
            options = s.get("service_options", [])
            return f"Please select 1-{len(options)}, or reply 'Skip'."

        result = await handle_selection_error(
            state,
            awaiting_step="awaiting_addon_selection",
            error_message_builder=build_error
        )
    """
    # Build error message
    if error_message_builder:
        error_msg = error_message_builder(state)
    else:
        error_msg = state.get("selection_error", default_error)

    logger.warning(f"⚠️ Selection error: {error_msg[:50]}...")

    # Send error message
    result = await send_message_node(state, lambda s: error_msg)

    # Pause workflow and set resume point
    result["should_proceed"] = False
    result["current_step"] = awaiting_step

    return result