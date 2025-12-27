"""Intent prediction metric for GEPA optimization.

Evaluates IntentPredictor module performance.
"""

import dspy
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def intent_metric(
    example: dspy.Example,
    pred: dspy.Prediction,
    trace: Optional[str] = None
) -> float:
    """Evaluate intent prediction quality.

    Scoring Components:
    - 0.5: Intent correctness (matches actual action taken)
    - 0.3: Confidence calibration
    - 0.2: Next step accuracy (predicted next step matches action)

    Args:
        example: Ground truth from BrainDecision
        pred: Model prediction with intent, confidence, next_step
        trace: Optional execution trace

    Returns:
        Score between 0.0 and 1.0
    """
    score = 0.0

    # Ground truth from BrainDecision
    predicted_intent = example.get("predicted_intent")  # What brain predicted
    action_taken = example.get("action_taken")  # What workflow actually did
    workflow_outcome = example.get("workflow_outcome")

    # Prediction from IntentPredictor
    pred_intent = pred.intent.strip().lower()
    pred_confidence = float(pred.confidence)
    pred_next_step = pred.next_step.strip().lower()

    # Component 1: Intent Correctness (0.5 points)
    # Intent categories: booking, modification, inquiry, complaint, unclear
    if predicted_intent:
        true_intent = predicted_intent.lower()
        if pred_intent == true_intent:
            score += 0.5
        elif _is_similar_intent(pred_intent, true_intent):
            score += 0.3  # Partial credit for similar intents
    else:
        # No ground truth, use action_taken as proxy
        if action_taken and _intent_matches_action(pred_intent, action_taken):
            score += 0.4

    # Component 2: Confidence Calibration (0.3 points)
    correct = (predicted_intent and pred_intent == predicted_intent.lower())

    if correct and pred_confidence > 0.7:
        score += 0.3
    elif correct and pred_confidence > 0.5:
        score += 0.15
    elif not correct and pred_confidence < 0.4:
        score += 0.2  # Good calibration on uncertain prediction

    # Component 3: Next Step Accuracy (0.2 points)
    if action_taken:
        action_lower = action_taken.lower()
        if pred_next_step in action_lower or action_lower in pred_next_step:
            score += 0.2
        elif _is_related_action(pred_next_step, action_lower):
            score += 0.1

    # Bonus: Successful outcome alignment
    if workflow_outcome == "success" and pred_confidence > 0.6:
        score += 0.05

    # Clamp to [0, 1]
    final_score = max(min(score, 1.0), 0.0)

    logger.debug(
        f"Intent metric: {final_score:.3f} "
        f"(pred={pred_intent}, conf={pred_confidence:.2f}, action={action_taken})"
    )

    return final_score


def _is_similar_intent(intent1: str, intent2: str) -> bool:
    """Check if two intents are semantically similar."""
    similar_pairs = [
        {"booking", "reservation", "schedule"},
        {"modification", "change", "update", "reschedule"},
        {"inquiry", "question", "ask", "clarification"},
        {"complaint", "issue", "problem"}
    ]

    for pair in similar_pairs:
        if intent1 in pair and intent2 in pair:
            return True
    return False


def _intent_matches_action(intent: str, action: str) -> bool:
    """Check if intent aligns with action taken."""
    action = action.lower()

    intent_action_map = {
        "booking": ["schedule", "book", "reserve", "appointment"],
        "modification": ["update", "change", "modify", "reschedule"],
        "inquiry": ["answer", "clarify", "explain", "provide"],
        "complaint": ["escalate", "resolve", "address"]
    }

    if intent in intent_action_map:
        return any(keyword in action for keyword in intent_action_map[intent])

    return False


def _is_related_action(next_step: str, action: str) -> bool:
    """Check if predicted next step is related to actual action."""
    related_keywords = [
        ("collect", "extract", "gather"),
        ("validate", "check", "verify"),
        ("confirm", "approve", "accept"),
        ("respond", "reply", "answer")
    ]

    for keywords in related_keywords:
        if any(k in next_step for k in keywords) and any(k in action for k in keywords):
            return True

    return False
