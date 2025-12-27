"""Log decision atomic node - RL Gym logging."""

import logging
from typing import Protocol
from datetime import datetime
import uuid
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

        # Create decision record
        decision = BrainDecision(
            decision_id=decision_id,
            conversation_id=state.get("conversation_id", "unknown"),
            timestamp=datetime.utcnow(),
            user_message=state.get("user_message", ""),
            conflict_detected=state.get("conflict_detected"),
            predicted_intent=state.get("predicted_intent"),
            proposed_response=state.get("proposed_response"),
            actual_response=state.get("response"),  # Workflow's response
            brain_confidence=state.get("brain_confidence", 0.0),
            conversation_quality=state.get("conversation_quality", 0.5),
            user_satisfaction=state.get("user_satisfaction"),
            workflow_outcome=None,  # Will be updated later
            dream_applied=state.get("dream_applied", False)
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
