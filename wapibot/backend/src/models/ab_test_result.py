"""A/B test result model - Shadow mode comparisons."""

from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class ABTestResult(BaseModel):
    """A/B test comparison between baseline and optimized modules.

    CRITICAL: Both variants run in shadow mode. Customer sees neither.
    """

    test_id: str = Field(description="Unique test identifier")
    test_name: str = Field(description="Test name (e.g., 'conflict_detector_v1.0')")
    conversation_id: str = Field(description="Conversation being tested")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Variant assignment
    assigned_variant: str = Field(description="Which variant was assigned (A or B)")
    variant_a: str = Field(description="Baseline version (e.g., 'v0.0')")
    variant_b: str = Field(description="Test version (e.g., 'v1.0')")

    # Outputs from both variants
    variant_a_output: Dict[str, Any] = Field(description="Baseline module output")
    variant_b_output: Dict[str, Any] = Field(description="Optimized module output")

    # Comparison metrics
    difference: Dict[str, Any] = Field(
        description="Differences between variants",
        default_factory=dict
    )

    # Evaluation
    metric_score_a: Optional[float] = Field(
        description="Metric score for variant A",
        default=None
    )
    metric_score_b: Optional[float] = Field(
        description="Metric score for variant B",
        default=None
    )
    winner: Optional[str] = Field(
        description="Which variant performed better (A or B)",
        default=None
    )

    # Actual outcome (filled later)
    workflow_outcome: Optional[str] = Field(default=None)
    user_satisfaction: Optional[float] = Field(default=None)

    class Config:
        json_schema_extra = {
            "example": {
                "test_id": "ab_123",
                "test_name": "conflict_detector_v1.0",
                "conversation_id": "conv_456",
                "assigned_variant": "B",
                "variant_a": "v0.0",
                "variant_b": "v1.0",
                "metric_score_a": 0.72,
                "metric_score_b": 0.85,
                "winner": "B"
            }
        }
