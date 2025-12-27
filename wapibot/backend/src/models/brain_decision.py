"""Brain decision record model for RL Gym."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class BrainDecision(BaseModel):
    """Record of a brain decision for RL learning.

    Stored in SQLite for offline GEPA optimization.
    """

    decision_id: str = Field(description="Unique decision identifier")
    conversation_id: str = Field(description="Conversation this decision belongs to")
    timestamp: datetime = Field(default_factory=datetime.now)

    # Input context
    user_message: str
    conversation_history: str  # JSON serialized
    state_snapshot: str  # JSON serialized

    # Brain outputs
    conflict_detected: Optional[str] = None
    predicted_intent: Optional[str] = None
    proposed_response: Optional[str] = None
    confidence: float = 0.0

    # Action taken
    brain_mode: str  # shadow | reflex | conscious
    action_taken: Optional[str] = None
    response_sent: Optional[str] = None

    # Outcome (filled later)
    user_response: Optional[str] = None
    workflow_outcome: Optional[str] = None  # success | failure | abandoned
    user_satisfaction: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "decision_id": "dec_123",
                "conversation_id": "conv_456",
                "user_message": "Can you give me a discount?",
                "brain_mode": "shadow",
                "conflict_detected": "bargaining"
            }
        }
