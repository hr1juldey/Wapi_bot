"""Brain state TypedDict - extends BookingState with brain fields."""

from typing import TypedDict, Optional, List


class BrainState(TypedDict, total=False):
    """Brain-specific state fields.

    These fields are added to BookingState when brain is enabled.
    All fields are optional (total=False) to avoid breaking existing workflows.
    """

    # Module outputs
    conflict_detected: Optional[str]  # "frustration" | "bargaining" | None
    predicted_intent: Optional[str]  # Predicted next user action
    conversation_quality: float  # 0.0 - 1.0
    decomposed_goals: List[str]  # Sub-goals identified
    proposed_response: Optional[str]  # Brain's proposed response

    # Control
    brain_mode: str  # "shadow" | "reflex" | "conscious"
    action_taken: Optional[str]  # What action brain took
    confidence: float  # Brain's confidence in decision

    # Learning
    brain_decision_id: Optional[str]  # UUID for RL tracking
    dream_applied: bool  # Was a dream learning applied?

    # Tracking
    brain_observation_count: int  # Number of times brain observed
    brain_action_count: int  # Number of times brain acted
    last_brain_action: Optional[str]  # Last action taken
