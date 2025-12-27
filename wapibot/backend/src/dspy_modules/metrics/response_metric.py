"""Response generation metric for GEPA optimization.

Evaluates ResponseGenerator module performance.
"""

import dspy
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def response_metric(
    example: dspy.Example,
    pred: dspy.Prediction,
    trace: Optional[str] = None
) -> float:
    """Evaluate response generation quality.

    Scoring Components:
    - 0.4: User satisfaction alignment
    - 0.3: Response appropriateness (length, tone)
    - 0.2: Confidence calibration
    - 0.1: Goal coverage (addresses sub-goals)

    Args:
        example: Ground truth from BrainDecision
        pred: Model prediction with proposed_response, confidence
        trace: Optional execution trace

    Returns:
        Score between 0.0 and 1.0
    """
    score = 0.0

    # Ground truth
    user_satisfaction = example.get("user_satisfaction")
    workflow_outcome = example.get("workflow_outcome")
    response_sent = example.get("response_sent")

    # Prediction
    pred_response = pred.proposed_response
    pred_confidence = float(pred.confidence)

    # Component 1: User Satisfaction (0.4 points)
    if user_satisfaction is not None:
        if user_satisfaction > 0.8:
            score += 0.4
        elif user_satisfaction > 0.6:
            score += 0.3
        elif user_satisfaction > 0.4:
            score += 0.2
        else:
            score += 0.1
    elif workflow_outcome == "success":
        score += 0.3

    # Component 2: Appropriateness (0.3 points)
    if pred_response:
        length = len(pred_response)
        # Good responses: 50-300 chars
        if 50 <= length <= 300:
            score += 0.15
        elif 30 <= length <= 400:
            score += 0.1

        # Check tone (polite, helpful)
        polite_words = ["please", "thank", "help", "assist", "would", "could"]
        if any(word in pred_response.lower() for word in polite_words):
            score += 0.15

    # Component 3: Confidence Calibration (0.2 points)
    if user_satisfaction is not None:
        high_satisfaction = user_satisfaction > 0.7
        if high_satisfaction and pred_confidence > 0.7:
            score += 0.2
        elif not high_satisfaction and pred_confidence < 0.5:
            score += 0.15

    # Component 4: Goal Coverage (0.1 points)
    if pred_response and response_sent:
        # Check if response addresses key topics
        key_topics = ["appointment", "booking", "service", "vehicle", "time", "date"]
        topics_covered = sum(1 for topic in key_topics if topic in pred_response.lower())
        if topics_covered >= 2:
            score += 0.1

    return max(min(score, 1.0), 0.0)
