"""Log decision atomic node - RL Gym logging."""

import logging
from typing import Protocol
from datetime import datetime
import uuid
import json
from models.brain_state import BrainState
from models.brain_decision import BrainDecision

logger = logging.getLogger(__name__)


class DecisionRepository(Protocol):
    """Protocol for decision repository."""

    def save(self, decision: BrainDecision) -> None:
        """Save decision to database."""
        ...


def node(
    state: BrainState,
    repo: DecisionRepository
) -> BrainState:
    """Atomic node: Log brain decision to RL Gym for learning.

    Records:
    - Brain's proposed action vs workflow's actual action
    - Conflict detected, intent predicted
    - User satisfaction and conversation quality
    - Outcome for reinforcement learning

    Args:
        state: Current brain state
        repo: DecisionRepository implementation

    Returns:
        Updated state with brain_decision_id
    """
    try:
        # Generate decision ID
        decision_id = str(uuid.uuid4())

        # Serialize conversation history and state snapshot
        history = state.get("history", [])
        conversation_history = json.dumps(history) if history else "[]"

        # Create state snapshot (key fields only)
        state_snapshot = json.dumps({
            "profile_complete": state.get("profile_complete", False),
            "vehicle_selected": state.get("vehicle_selected", False),
            "service_selected": state.get("service_selected", False),
            "slot_selected": state.get("slot_selected", False),
            "confirmed": state.get("confirmed")
        })

        # Create decision record
        decision = BrainDecision(
            decision_id=decision_id,
            conversation_id=state.get("conversation_id", "unknown"),
            timestamp=datetime.utcnow(),
            user_message=state.get("user_message", ""),
            conversation_history=conversation_history,
            state_snapshot=state_snapshot,
            conflict_detected=state.get("conflict_detected"),
            predicted_intent=state.get("predicted_intent"),
            proposed_response=state.get("proposed_response"),
            confidence=state.get("brain_confidence", 0.0),
            brain_mode=state.get("brain_mode", "shadow"),
            action_taken=state.get("action_taken"),
            response_sent=state.get("response"),
            user_satisfaction=state.get("user_satisfaction"),
            workflow_outcome=None  # Will be updated later
        )

        # Save to RL Gym database
        repo.save(decision)

        # Update state
        state["brain_decision_id"] = decision_id

        logger.info(f"Decision logged to RL Gym: {decision_id}")

        return state

    except Exception as e:
        logger.error(f"Log decision failed: {e}")
        state["brain_decision_id"] = None
        return state
