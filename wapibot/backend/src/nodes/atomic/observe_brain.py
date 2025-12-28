"""Atomic brain observation node - records brain decisions.

Reusable across ALL nodes for consistent brain observation.
Configuration over duplication - Blender principle.

Usage:
    # Observe extraction decision
    observe_brain.node(state, "extraction.brain_obs", {
        "method_used": "dspy",
        "confidence": 0.9
    })

    # Observe merge decision (SAME node, different data!)
    observe_brain.node(state, "merge.brain_obs", {
        "merge_decision": "kept_existing",
        "confidence_delta": -0.2
    })

    # Any brain observation!
"""

import logging
from typing import Any, Dict, Optional
from workflows.shared.state import BookingState
from core.brain_config import get_brain_settings
from utils.field_utils import set_nested_field

logger = logging.getLogger(__name__)


async def node(
    state: BookingState,
    observation_path: str,
    observation_data: Optional[Dict[str, Any]] = None
) -> BookingState:
    """Atomic brain observation node - records brain mode and decisions.

    Single Responsibility: ONLY records brain observations (doesn't extract, validate, etc.)

    Args:
        state: Current booking state
        observation_path: Where to store observation (e.g., "extraction.brain_obs")
        observation_data: Optional additional data to record

    Returns:
        Updated state with brain observation metadata

    Examples:
        # Simple observation (just brain mode)
        await observe_brain.node(state, "step.brain_obs")

        # With custom data
        await observe_brain.node(state, "merge.brain_obs", {
            "merge_decision": "merged",
            "confidence_delta": 0.3
        })
    """
    brain_settings = get_brain_settings()

    # Build observation metadata
    metadata = {
        "brain_mode": brain_settings.brain_mode,
        "brain_enabled": brain_settings.brain_enabled
    }

    # Merge custom observation data if provided
    if observation_data:
        metadata.update(observation_data)

    # Store observation
    set_nested_field(state, observation_path, metadata)

    logger.debug(f"📊 Brain observation recorded at {observation_path}")

    return state