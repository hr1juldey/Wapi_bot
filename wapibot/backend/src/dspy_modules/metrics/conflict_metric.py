"""Conflict detection metric for GEPA optimization.

Evaluates ConflictDetector module performance.
"""

import dspy
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def conflict_metric(
    example: dspy.Example,
    pred: dspy.Prediction,
    trace: Optional[str] = None
) -> float:
    """Evaluate conflict detection prediction quality.

    Scoring Components:
    - 0.5: Correctness (detected conflict when present, no false positives)
    - 0.3: Confidence calibration (high when correct, low when wrong)
    - 0.2: Reasoning quality (mentions key conflict signals)

    Args:
        example: Ground truth from BrainDecision
        pred: Model prediction with conflict_type, confidence, reasoning
        trace: Optional execution trace

    Returns:
        Score between 0.0 and 1.0
    """
    score = 0.0

    # Ground truth from BrainDecision
    true_conflict = example.get("conflict_detected")  # "user_disagreement" or None
    workflow_outcome = example.get("workflow_outcome")  # "success" or "failure"

    # Prediction from ConflictDetector
    pred_conflict = pred.conflict_type.strip().lower()
    pred_confidence = float(pred.confidence)
    pred_reasoning = pred.reasoning.lower()

    # Component 1: Correctness (0.5 points)
    if true_conflict:
        # Should detect conflict (not "no")
        if pred_conflict != "no":
            score += 0.5
    else:
        # Should NOT detect conflict (must be "no")
        if pred_conflict == "no":
            score += 0.5

    # Component 2: Confidence Calibration (0.3 points)
    # High confidence when correct, low confidence when wrong
    correct = (true_conflict and pred_conflict != "no") or (not true_conflict and pred_conflict == "no")

    if correct and pred_confidence > 0.7:
        score += 0.3
    elif correct and pred_confidence > 0.5:
        score += 0.15
    elif not correct and pred_confidence < 0.3:
        score += 0.2  # Good calibration on wrong prediction

    # Component 3: Reasoning Quality (0.2 points)
    # Check if reasoning mentions key conflict signals
    reasoning_signals = [
        "disagree", "no", "wrong", "incorrect", "change",
        "different", "not", "contradict"
    ]

    if true_conflict:
        # Should mention conflict-related words
        if any(signal in pred_reasoning for signal in reasoning_signals):
            score += 0.2
    else:
        # Should NOT overuse conflict words for non-conflicts
        conflict_words = sum(1 for signal in reasoning_signals if signal in pred_reasoning)
        if conflict_words == 0:
            score += 0.2
        elif conflict_words == 1:
            score += 0.1

    # Bonus: Workflow outcome alignment (optional, not counted in base score)
    if workflow_outcome == "failure" and pred_conflict != "no":
        score += 0.05  # Extra credit for detecting problematic conversations

    # Clamp to [0, 1]
    final_score = max(min(score, 1.0), 0.0)

    logger.debug(
        f"Conflict metric: {final_score:.3f} "
        f"(true={true_conflict}, pred={pred_conflict}, conf={pred_confidence:.2f})"
    )

    return final_score
