"""Sentiment analysis domain models.

Provides validated models for sentiment scores with
decision logic for conversation flow control.
"""

from typing import Dict
from enum import Enum
from pydantic import BaseModel, Field, model_validator, ConfigDict
from models.core import ExtractionMetadata


class SentimentDimension(str, Enum):
    """Sentiment dimensions to track."""

    INTEREST = "interest"
    DISGUST = "disgust"
    ANGER = "anger"
    BOREDOM = "boredom"
    NEUTRAL = "neutral"


class SentimentScores(BaseModel):
    """Validated sentiment scores with decision logic."""

    model_config = ConfigDict(extra='forbid')

    interest: float = Field(
        ge=1.0,
        le=10.0,
        description="Interest level (1-10)"
    )
    anger: float = Field(
        ge=1.0,
        le=10.0,
        description="Anger level (1-10)"
    )
    disgust: float = Field(
        ge=1.0,
        le=10.0,
        description="Disgust level (1-10)"
    )
    boredom: float = Field(
        ge=1.0,
        le=10.0,
        description="Boredom level (1-10)"
    )
    neutral: float = Field(
        ge=1.0,
        le=10.0,
        description="Neutral level (1-10)"
    )
    reasoning: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Sentiment analysis reasoning"
    )
    metadata: ExtractionMetadata = Field(
        description="Extraction metadata"
    )

    @model_validator(mode='after')
    def validate_sentiment_ranges(self):
        """Validate all sentiment scores in valid range."""
        for field in ["interest", "anger", "disgust", "boredom", "neutral"]:
            value = getattr(self, field)
            if not (1.0 <= value <= 10.0):
                raise ValueError(
                    f"{field} score must be between 1.0 and 10.0"
                )
        return self

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "interest": self.interest,
            "anger": self.anger,
            "disgust": self.disgust,
            "boredom": self.boredom,
            "neutral": self.neutral,
        }

    def should_proceed(self) -> bool:
        """Determine if conversation should proceed normally."""
        # Thresholds for proceeding
        if self.anger >= 7.0 or self.disgust >= 7.0 or self.boredom >= 8.0:
            return False

        return self.interest >= 4.0

    def should_disengage(self) -> bool:
        """Determine if conversation should disengage."""
        return (
            self.anger >= 8.0
            or self.disgust >= 8.0
            or self.boredom >= 9.0
        )

    def needs_engagement(self) -> bool:
        """Determine if conversation needs more engagement."""
        return self.interest >= 7.0
