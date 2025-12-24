"""Intent classification domain models.

Provides validated models for user intent classification
with confidence scoring and decision logic.
"""

from typing import Literal
from pydantic import BaseModel, Field, computed_field, ConfigDict
from models.core import ExtractionMetadata


class IntentClass(str):
    """Valid intent classes for user messages."""

    BOOK = "book"
    INQUIRE = "inquire"
    COMPLAINT = "complaint"
    SMALL_TALK = "small_talk"
    CANCEL = "cancel"
    RESCHEDULE = "reschedule"
    PAYMENT = "payment"


class Intent(BaseModel):
    """Validated intent classification with confidence."""

    model_config = ConfigDict(extra='forbid')

    intent_class: Literal[
        "book",
        "inquire",
        "complaint",
        "small_talk",
        "cancel",
        "reschedule",
        "payment"
    ] = Field(..., description="Classified intent")
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Classification confidence"
    )
    reasoning: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Classification reasoning"
    )
    metadata: ExtractionMetadata = Field(
        description="Extraction metadata"
    )

    @computed_field
    @property
    def is_high_confidence(self) -> bool:
        """Check if classification has high confidence."""
        return self.confidence >= 0.8

    @computed_field
    @property
    def is_low_confidence(self) -> bool:
        """Check if classification has low confidence."""
        return self.confidence < 0.5
