"""Atomic checkpoint node - milestone-based state persistence.

SOLID Principles:
- Single Responsibility: ONLY saves state at important milestones
- Open/Closed: Extensible via checkpoint types
- Interface Segregation: Simple checkpoint interface

Blender Design:
- Atomic operation for state persistence
- Brain uses checkpoints to learn successful vs failed paths
- Enables conversation replay for debugging
- Triggers on milestone events or errors
"""

import logging
import json
import uuid
from datetime import datetime
from workflows.shared.state import BookingState
from core.brain_config import get_brain_settings
from repositories.brain_decision_repo import BrainDecisionRepository
from models.brain_decision import BrainDecision

logger = logging.getLogger(__name__)


async def node(
    state: BookingState,
    checkpoint_name: str,
    checkpoint_type: str = "milestone",
    save_to_brain: bool = True
) -> BookingState:
    """Atomic checkpoint node - saves state at milestones for debugging and learning.

    Saves state snapshots at important workflow milestones:
    - customer_confirmed: After customer name/phone collected
    - vehicle_selected: After vehicle chosen
    - slot_selected: After appointment time selected
    - booking_created: After booking successfully created
    - error_occurred: On workflow errors for debugging

    Brain uses these checkpoints to:
    - Learn successful conversation paths
    - Identify where users drop off
    - Replay conversations for debugging

    Args:
        state: Current booking state
        checkpoint_name: Name of this checkpoint (e.g., "customer_confirmed")
        checkpoint_type: Type ("milestone", "error", "decision_point")
        save_to_brain: Whether to save checkpoint for brain learning

    Returns:
        State with checkpoint metadata added

    Examples:
        # After customer info collected
        await checkpoint.node(state, "customer_confirmed", "milestone")

        # After booking created
        await checkpoint.node(state, "booking_created", "milestone")

        # On error
        await checkpoint.node(state, "validation_error", "error")
    """
    brain_settings = get_brain_settings()

    # Build checkpoint metadata
    checkpoint = {
        "name": checkpoint_name,
        "type": checkpoint_type,
        "timestamp": datetime.utcnow().isoformat(),
        "conversation_id": state.get("conversation_id"),
        "current_step": state.get("current_step"),
        "completeness": state.get("completeness", 0.0),
        "errors": state.get("errors", [])
    }

    # Log checkpoint
    logger.info(f"💾 Checkpoint: {checkpoint_name} ({checkpoint_type})")

    # Add to state's checkpoint history
    if "checkpoints" not in state:
        state["checkpoints"] = []
    state["checkpoints"].append(checkpoint)

    # Save to brain memory for learning (Phase 4 Integration)
    # Brain will analyze checkpoint sequences to learn:
    # - Which paths lead to successful bookings
    # - Where users abandon conversations
    # - Common error patterns
    if save_to_brain and brain_settings.brain_enabled and brain_settings.rl_gym_enabled:
        try:
            # Create brain decision record for this checkpoint
            decision = BrainDecision(
                decision_id=f"chk_{uuid.uuid4().hex[:8]}",
                conversation_id=state.get("conversation_id", "unknown"),
                user_message=state.get("user_message", ""),
                conversation_history=json.dumps(state.get("history", [])[-5:]),  # Last 5 messages
                state_snapshot=json.dumps({
                    "completeness": state.get("completeness", 0.0),
                    "current_step": state.get("current_step"),
                    "errors": state.get("errors", [])
                }),
                brain_mode=brain_settings.brain_mode,
                action_taken=f"checkpoint:{checkpoint_name}",
                workflow_outcome=checkpoint_type  # milestone | error | decision_point
            )

            # Save to RL Gym database
            repo = BrainDecisionRepository()
            repo.save(decision)
            logger.debug(f"🧠 Checkpoint saved to brain_gym.db: {checkpoint_name}")
        except Exception as e:
            logger.warning(f"⚠️ Failed to save checkpoint to brain memory: {e}")

    return state