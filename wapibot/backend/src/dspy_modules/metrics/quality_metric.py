"""Quality evaluation metric for GEPA optimization.

Evaluates QualityEvaluator module performance.
"""

import dspy
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def quality_metric(
    example: dspy.Example,
    pred: dspy.Prediction,
    trace: Optional[str] = None
) -> float:
    """Evaluate quality assessment accuracy.

    Scoring Components:
    - 0.4: Quality score alignment (matches user satisfaction)
    - 0.3: Issue identification (finds actual problems)
    - 0.2: Confidence calibration
    - 0.1: Actionable suggestions

    Args:
        example: Ground truth from BrainDecision
        pred: Model prediction with quality_score, issues, suggestions
        trace: Optional execution trace

    Returns:
        Score between 0.0 and 1.0
    """
    score = 0.0

    # Ground truth from BrainDecision
    user_satisfaction = example.get("user_satisfaction")
    workflow_outcome = example.get("workflow_outcome")
    conflict_detected = example.get("conflict_detected")

    # Prediction from QualityEvaluator
    pred_quality = float(pred.quality_score)
    pred_confidence = float(pred.confidence)
    pred_issues = pred.issues.lower()

    # Component 1: Quality Score Alignment (0.4 points)
    if user_satisfaction is not None:
        diff = abs(pred_quality - user_satisfaction)
        if diff < 0.1:
            score += 0.4
        elif diff < 0.2:
            score += 0.3
        elif diff < 0.3:
            score += 0.2
        else:
            score += 0.1
    else:
        if workflow_outcome == "success" and pred_quality > 0.7:
            score += 0.3
        elif workflow_outcome == "failure" and pred_quality < 0.5:
            score += 0.3

    # Component 2: Issue Identification (0.3 points)
    actual_problems = []
    if conflict_detected:
        actual_problems.append("conflict")
    if workflow_outcome == "failure":
        actual_problems.append("failure")

    if actual_problems:
        issue_keywords = ["conflict", "disagree", "unclear", "error", "fail"]
        if any(kw in pred_issues for kw in issue_keywords):
            score += 0.3
    else:
        if "no issues" in pred_issues or len(pred_issues) < 20:
            score += 0.3

    # Component 3: Confidence Calibration (0.2 points)
    if user_satisfaction is not None:
        accurate = abs(pred_quality - user_satisfaction) < 0.2
        if accurate and pred_confidence > 0.7:
            score += 0.2

    # Component 4: Suggestions (0.1 points)
    if actual_problems and len(pred.get("suggestions", "")) > 20:
        score += 0.1

    return max(min(score, 1.0), 0.0)
