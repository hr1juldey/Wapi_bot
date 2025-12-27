"""Recall memories atomic node - Dream memory retrieval."""

import logging
from typing import Protocol, List, Dict, Any
from models.brain_state import BrainState

logger = logging.getLogger(__name__)


class MemoryRepository(Protocol):
    """Protocol for memory repository."""

    def get_recent(self, limit: int) -> List[Dict[str, Any]]:
        """Get recent memories for dream processing."""
        ...


def node(
    state: BrainState,
    repo: MemoryRepository,
    min_memories: int = 50
) -> BrainState:
    """Atomic node: Recall memories for dream processing.

    Retrieves:
    - Recent conversation outcomes
    - Booking successes/failures
    - User satisfaction patterns
    - Decision history

    Args:
        state: Current brain state
        repo: MemoryRepository implementation
        min_memories: Minimum memories required for dreaming

    Returns:
        Updated state with recalled_memories field
    """
    try:
        # Fetch recent memories
        memories = repo.get_recent(limit=100)

        # Check if enough memories
        if len(memories) < min_memories:
            logger.info(f"Not enough memories: {len(memories)}/{min_memories}")
            state["recalled_memories"] = []
            state["can_dream"] = False
            return state

        # Sort by importance (user_satisfaction, conversation_quality)
        sorted_memories = sorted(
            memories,
            key=lambda m: (
                m.get("user_satisfaction", 0.0) * 0.6 +
                m.get("conversation_quality", 0.0) * 0.4
            ),
            reverse=True
        )

        # Update state
        state["recalled_memories"] = sorted_memories[:min_memories]
        state["can_dream"] = True

        logger.info(f"Recalled {len(state['recalled_memories'])} memories for dreaming")

        return state

    except Exception as e:
        logger.error(f"Recall memories failed: {e}")
        state["recalled_memories"] = []
        state["can_dream"] = False
        return state
