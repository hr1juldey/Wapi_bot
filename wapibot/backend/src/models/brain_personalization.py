"""Brain personalization model - Shadow mode suggestions only."""

from typing import List, Optional
from pydantic import BaseModel, Field


class PersonalizationSuggestion(BaseModel):
    """Personalization suggestion for a message.

    CRITICAL: This is logged ONLY, never sent to customers.
    """

    suggestion_id: str = Field(description="Unique suggestion identifier")
    conversation_id: str = Field(description="Associated conversation")

    # Original vs personalized
    original_message: str = Field(description="Baseline message")
    personalized_message: str = Field(description="Suggested personalized version")

    # What changed
    modifications: List[str] = Field(
        description="List of modifications made",
        default_factory=list
    )

    # Confidence and reasoning
    confidence: float = Field(
        description="Confidence in personalization (0.0-1.0)",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(description="Why this personalization was suggested")

    # Context
    customer_profile: Optional[dict] = Field(
        description="Customer profile used for personalization",
        default=None
    )

    # Outcome (filled later)
    was_better: Optional[bool] = Field(
        description="Whether personalization would have been better",
        default=None
    )
    user_satisfaction: Optional[float] = Field(
        description="Actual user satisfaction with baseline",
        default=None
    )

    class Config:
        json_schema_extra = {
            "example": {
                "suggestion_id": "pers_123",
                "conversation_id": "conv_456",
                "original_message": "Your appointment is confirmed.",
                "personalized_message": "Great news! Your appointment is all set 👍",
                "modifications": ["added_enthusiasm", "added_emoji"],
                "confidence": 0.85,
                "reasoning": "Customer prefers casual, friendly tone based on history"
            }
        }
