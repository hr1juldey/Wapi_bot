"""Pydantic schemas for Brain Control API."""

from typing import Literal, Optional, List
from pydantic import BaseModel, Field
from schemas.examples import (
    EXAMPLE_DREAM_TASK_ID,
    EXAMPLE_TRAIN_TASK_ID,
    EXAMPLE_DECISION_COUNT,
    EXAMPLE_CONVERSATION_THRESHOLD,
)


class DreamTriggerRequest(BaseModel):
    """Request to manually trigger dream cycle."""

    force: bool = Field(
        default=False,
        description="Force dream even if minimum conversations not met",
        examples=[False, True],
    )
    min_conversations: Optional[int] = Field(
        default=None,
        description="Override minimum conversations threshold",
        examples=[EXAMPLE_CONVERSATION_THRESHOLD, 100, 200],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "force": False,
                "min_conversations": EXAMPLE_CONVERSATION_THRESHOLD,
            }
        }


class TrainTriggerRequest(BaseModel):
    """Request to trigger GEPA optimization."""

    optimizer: Literal["gepa"] = Field(
        default="gepa", description="Optimization algorithm to use", examples=["gepa"]
    )
    num_iterations: int = Field(
        default=100,
        ge=1,
        description="Number of training iterations",
        examples=[100, 200, 500],
    )

    class Config:
        json_schema_extra = {"example": {"optimizer": "gepa", "num_iterations": 100}}


class FeatureToggleUpdate(BaseModel):
    """Update a feature toggle."""

    feature_name: str = Field(
        ...,
        description="Name of feature to toggle",
        examples=["brain_enabled", "rl_gym_enabled", "dream_enabled"],
    )
    enabled: bool = Field(
        ..., description="Enable or disable the feature", examples=[True, False]
    )

    class Config:
        json_schema_extra = {
            "example": {"feature_name": "brain_enabled", "enabled": True}
        }


class BrainModeUpdate(BaseModel):
    """Update brain operation mode."""

    mode: Literal["shadow", "reflex", "conscious"] = Field(
        ...,
        description="Brain operation mode (shadow=observe, reflex=auto, conscious=hybrid)",
        examples=["shadow", "reflex", "conscious"],
    )

    class Config:
        json_schema_extra = {"example": {"mode": "shadow"}}


class BrainStatusResponse(BaseModel):
    """Brain system status."""

    enabled: bool = Field(..., description="Whether brain is enabled", examples=[True])
    mode: str = Field(
        ...,
        description="Current operation mode",
        examples=["shadow", "reflex", "conscious"],
    )
    features: dict = Field(
        ...,
        description="Feature toggle states",
        examples=[
            {
                "brain_enabled": True,
                "rl_gym_enabled": True,
                "dream_enabled": True,
            }
        ],
    )
    metrics: dict = Field(
        ...,
        description="System metrics and counters",
        examples=[
            {
                "total_decisions": EXAMPLE_DECISION_COUNT,
                "last_dream_at": "2025-12-27T03:00:00",
            }
        ],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "enabled": True,
                "mode": "shadow",
                "features": {
                    "brain_enabled": True,
                    "rl_gym_enabled": True,
                    "dream_enabled": True,
                },
                "metrics": {
                    "total_decisions": EXAMPLE_DECISION_COUNT,
                    "last_dream_at": "2025-12-27T03:00:00",
                },
            }
        }


class DecisionRecord(BaseModel):
    """Single brain decision record."""

    decision_id: str = Field(
        ..., description="Unique decision identifier", examples=["DEC-2025-001"]
    )
    timestamp: str = Field(
        ...,
        description="ISO timestamp of decision",
        examples=["2025-12-27T14:30:00.123456"],
    )
    conflict_detected: Optional[str] = Field(
        None,
        description="Type of conflict detected (if any)",
        examples=["extraction_mismatch", None],
    )
    action_taken: Optional[str] = Field(
        None,
        description="Action taken by brain",
        examples=["merged_history", "used_llm", None],
    )
    confidence: float = Field(
        ...,
        description="Decision confidence score (0.0-1.0)",
        examples=[0.95, 0.75, 0.5],
    )

    class Config:
        json_schema_extra = {
            "example": {
                "decision_id": "DEC-2025-001",
                "timestamp": "2025-12-27T14:30:00.123456",
                "conflict_detected": "extraction_mismatch",
                "action_taken": "merged_history",
                "confidence": 0.95,
            }
        }


class DecisionListResponse(BaseModel):
    """Paginated decision history."""

    decisions: List[DecisionRecord] = Field(
        ..., description="List of decision records for current page"
    )
    total: int = Field(..., description="Total number of decisions", examples=[1523])
    page: int = Field(..., description="Current page number", examples=[1])
    page_size: int = Field(..., description="Records per page", examples=[20])

    class Config:
        json_schema_extra = {
            "example": {
                "decisions": [
                    {
                        "decision_id": "DEC-2025-001",
                        "timestamp": "2025-12-27T14:30:00.123456",
                        "conflict_detected": "extraction_mismatch",
                        "action_taken": "merged_history",
                        "confidence": 0.95,
                    }
                ],
                "total": EXAMPLE_DECISION_COUNT,
                "page": 1,
                "page_size": 20,
            }
        }
