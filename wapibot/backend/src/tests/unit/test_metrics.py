"""Unit tests for GEPA metric functions."""

import pytest
import dspy
from dspy_modules.metrics import (
    conflict_metric,
    intent_metric,
    quality_metric,
    goals_metric,
    response_metric
)


def test_conflict_metric_detects_conflict():
    """Test conflict metric when conflict is detected."""
    example = dspy.Example(
        conflict_detected="user_disagreement",
        workflow_outcome="failure"
    )

    pred = dspy.Prediction(
        conflict_type="user_disagreement",
        confidence=0.85,
        reasoning="User said 'no that's wrong'"
    )

    score = conflict_metric(example, pred)
    assert 0.7 <= score <= 1.0, f"Expected high score, got {score}"


def test_conflict_metric_no_conflict():
    """Test conflict metric when no conflict exists."""
    example = dspy.Example(
        conflict_detected=None,
        workflow_outcome="success"
    )

    pred = dspy.Prediction(
        conflict_type="no",
        confidence=0.9,
        reasoning="Conversation flowing smoothly"
    )

    score = conflict_metric(example, pred)
    assert 0.7 <= score <= 1.0, f"Expected high score, got {score}"


def test_intent_metric_correct_prediction():
    """Test intent metric with correct prediction."""
    example = dspy.Example(
        predicted_intent="booking",
        action_taken="schedule_appointment",
        workflow_outcome="success"
    )

    pred = dspy.Prediction(
        intent="booking",
        confidence=0.9,
        next_step="schedule appointment"
    )

    score = intent_metric(example, pred)
    assert 0.6 <= score <= 1.0, f"Expected high score, got {score}"


def test_quality_metric_high_satisfaction():
    """Test quality metric with high user satisfaction."""
    example = dspy.Example(
        user_satisfaction=0.9,
        workflow_outcome="success",
        conflict_detected=None
    )

    pred = dspy.Prediction(
        quality_score=0.85,
        confidence=0.8,
        issues="no issues detected",
        suggestions=""
    )

    score = quality_metric(example, pred)
    assert 0.6 <= score <= 1.0, f"Expected high score, got {score}"


def test_goals_metric_aligned_goals():
    """Test goals metric with aligned sub-goals."""
    import json

    example = dspy.Example(
        action_taken="extract_customer_info",
        state_snapshot=json.dumps({
            "profile_complete": False,
            "vehicle_selected": False
        }),
        workflow_outcome="success"
    )

    pred = dspy.Prediction(
        sub_goals=["extract customer name", "collect phone number"],
        required_info=["profile", "contact details"]
    )

    score = goals_metric(example, pred)
    assert 0.3 <= score <= 1.0, f"Expected reasonable score, got {score}"


def test_response_metric_good_response():
    """Test response metric with high satisfaction."""
    example = dspy.Example(
        user_satisfaction=0.85,
        workflow_outcome="success",
        response_sent="I can help you schedule an appointment"
    )

    pred = dspy.Prediction(
        proposed_response="I'd be happy to help you book an appointment. What date works for you?",
        confidence=0.8
    )

    score = response_metric(example, pred)
    assert 0.4 <= score <= 1.0, f"Expected high score, got {score}"


def test_all_metrics_return_valid_range():
    """Test that all metrics return scores in [0, 1]."""
    import json

    example = dspy.Example(
        conflict_detected="user_disagreement",
        predicted_intent="booking",
        action_taken="extract_info",
        user_satisfaction=0.7,
        workflow_outcome="success",
        state_snapshot=json.dumps({"profile_complete": True}),
        response_sent="Test response"
    )

    pred = dspy.Prediction(
        conflict_type="user_disagreement",
        intent="booking",
        quality_score=0.75,
        sub_goals=["extract data"],
        required_info=["name"],
        proposed_response="I can help with that",
        confidence=0.8,
        reasoning="Test reasoning",
        issues="none",
        suggestions="",
        next_step="extract"
    )

    scores = [
        conflict_metric(example, pred),
        intent_metric(example, pred),
        quality_metric(example, pred),
        goals_metric(example, pred),
        response_metric(example, pred)
    ]

    for i, score in enumerate(scores):
        assert 0.0 <= score <= 1.0, f"Metric {i} returned invalid score: {score}"
