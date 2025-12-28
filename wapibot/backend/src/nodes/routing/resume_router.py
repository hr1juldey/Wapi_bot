"""Resume routing factory - generates routing functions for node group entry points.

SOLID Principles:
- Single Responsibility: ONLY creates resume/fresh routing logic
- Open/Closed: Extensible via different check strategies
- Dependency Inversion: Accepts callable predicates

DRY Principle:
- ONE implementation for ALL node group resume routing
- Eliminates ~160 lines of duplicated routing code across 8 node groups

Blender Architecture:
- Generic routing factory (like Blender's routing nodes)
- Configurable via parameters, not hardcoding
"""

import logging
from typing import Callable, Optional, Any
from workflows.shared.state import BookingState

logger = logging.getLogger(__name__)


def create_resume_router(
    awaiting_step: str,
    resume_node: str,
    fresh_node: str,
    readiness_check: Optional[Callable[[BookingState], bool]] = None,
    router_name: str = "resume_router"
) -> Callable[[BookingState], str]:
    """Factory: Create a resume/fresh routing function for node group entry.

    This eliminates duplicated routing logic across node groups by providing
    a configurable routing function generator.

    Args:
        awaiting_step: Value of current_step to check for resume (e.g., "awaiting_service_selection")
        resume_node: Node name to route to when resuming (e.g., "process_selection")
        fresh_node: Node name to route to when starting fresh (e.g., "fetch_services")
        readiness_check: Optional function to check if ready to resume
                        If None, only checks current_step match
        router_name: Name for logging (default: "resume_router")

    Returns:
        Routing function compatible with LangGraph conditional_edges

    Examples:
        # Simple resume check (only current_step)
        route_entry = create_resume_router(
            awaiting_step="awaiting_service_selection",
            resume_node="process_selection",
            fresh_node="fetch_services"
        )

        # Resume with readiness check
        route_entry = create_resume_router(
            awaiting_step="awaiting_addon_selection",
            resume_node="extract_selection",
            fresh_node="fetch_addons",
            readiness_check=lambda s: not s.get("addon_selection_complete", False)
        )
    """
    def route_entry(state: BookingState) -> str:
        """Route based on whether we're resuming or starting fresh."""
        current_step = state.get("current_step", "")

        # Check if resuming
        is_resuming = current_step == awaiting_step

        # Apply readiness check if provided
        if is_resuming and readiness_check:
            is_ready = readiness_check(state)
            if not is_ready:
                # Not ready to resume, start fresh
                logger.info(f"🔀 {router_name}: Readiness check failed, starting fresh")
                return fresh_node

        if is_resuming:
            logger.info(f"🔀 {router_name}: Resuming from {awaiting_step} → {resume_node}")
            return resume_node
        else:
            logger.info(f"🔀 {router_name}: Starting fresh → {fresh_node}")
            return fresh_node

    return route_entry