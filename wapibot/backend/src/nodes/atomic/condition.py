"""Atomic condition node - generic conditional routing with brain awareness.

SOLID Principles:
- Single Responsibility: ONLY evaluates conditions and routes workflow
- Open/Closed: Extensible via predicate functions
- Dependency Inversion: Depends on Predicate Protocol, not concrete implementations

Blender Design:
- Simple, atomic operation
- Composable with any predicate function
- Brain observes condition patterns for learning

Replaces inline if/else logic in node groups.
"""

import logging
from typing import Protocol
from workflows.shared.state import BookingState
from core.brain_config import get_brain_settings

logger = logging.getLogger(__name__)


class Predicate(Protocol):
    """Protocol for condition predicates.

    Any callable that takes state and returns bool is a valid Predicate.
    """

    def __call__(self, state: BookingState) -> bool:
        """Evaluate condition based on state.

        Args:
            state: Current booking state

        Returns:
            True if condition met, False otherwise
        """
        ...


async def node(
    state: BookingState,
    predicate: Predicate,
    condition_name: str = "unnamed_condition",
    respect_brain_mode: bool = True
) -> BookingState:
    """Atomic condition evaluation node - works with ANY predicate function.

    Single Responsibility: ONLY evaluates conditions and logs for brain learning.
    Does NOT route - that's done by LangGraph conditional_edges.

    Args:
        state: Current booking state
        predicate: ANY callable implementing Predicate protocol
        condition_name: Human-readable condition name for logging
        respect_brain_mode: Whether to log to brain for learning

    Returns:
        Updated state with condition_result field

    Examples:
        # Simple field check
        await condition.node(state, lambda s: s.get("confirmed") is True, "booking_confirmed")

        # Complex business logic
        def should_skip_addons(s):
            service = s.get("selected_service", {})
            return service.get("product_name") == "Basic Wash"

        await condition.node(state, should_skip_addons, "skip_addons_for_basic")
    """
    # Evaluate condition
    try:
        result = predicate(state)
        logger.info(f"🔀 Condition '{condition_name}': {result}")

        # Store result in state for routing
        state["condition_result"] = result
        state["last_condition_name"] = condition_name

        # Brain observation for pattern learning
        if respect_brain_mode:
            brain_settings = get_brain_settings()
            if brain_settings.brain_enabled:
                # Log condition for brain learning
                # Brain learns: "Users usually skip addons for service X"
                # Brain learns: "Confirmation rate higher in morning slots"
                logger.debug(f"🧠 Brain observing condition: {condition_name}={result}")

                # TODO: Integrate with brain observation system
                # This will be wired in Phase 4 Step 29

        return state

    except Exception as e:
        logger.error(f"❌ Condition '{condition_name}' evaluation failed: {e}")
        # Default to False on error
        state["condition_result"] = False
        state["last_condition_name"] = condition_name
        state["condition_error"] = str(e)
        return state