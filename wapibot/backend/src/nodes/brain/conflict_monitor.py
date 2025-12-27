"""Conflict monitor atomic node - ACC-like function."""

import logging
from typing import Protocol
from models.brain_state import BrainState

logger = logging.getLogger(__name__)


class ConflictDetector(Protocol):
    """Protocol for conflict detection modules."""

    def forward(self, conversation_history: list, user_message: str) -> dict:
        """Detect conflict in user message.

        Returns:
            Dict with conflict_type, confidence, reasoning
        """
        ...


def node(
    state: BrainState,
    detector: ConflictDetector
) -> BrainState:
    """Atomic node: Detect conflicts in user message.

    Uses ACC-like function to detect:
    - frustration, confusion, bargaining
    - off_topic, cancellation intent

    Args:
        state: Current brain state
        detector: ConflictDetector implementation (DSPy module)

    Returns:
        Updated state with conflict_detected field
    """
    try:
        # Extract conversation context
        history = state.get("history", [])
        user_message = state.get("user_message", "")

        if not user_message:
            logger.warning("No user message in state")
            state["conflict_detected"] = None
            return state

        # Run conflict detection
        result = detector(
            conversation_history=history,
            user_message=user_message
        )

        # Update state
        conflict_type = result.get("conflict_type", "none")
        if conflict_type == "none":
            state["conflict_detected"] = None
        else:
            state["conflict_detected"] = conflict_type

        # Store confidence for logging
        state["brain_confidence"] = result.get("confidence", 0.0)

        logger.info(f"Conflict detected: {conflict_type} (confidence: {result.get('confidence', 0.0)})")

        return state

    except Exception as e:
        logger.error(f"Conflict monitor failed: {e}")
        state["conflict_detected"] = None
        state["brain_confidence"] = 0.0
        return state
