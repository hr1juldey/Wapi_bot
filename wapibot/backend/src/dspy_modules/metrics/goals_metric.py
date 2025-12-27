"""Goal decomposition metric for GEPA optimization.

Evaluates GoalDecomposer module performance.
"""

import dspy
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def goals_metric(
    example: dspy.Example,
    pred: dspy.Prediction,
    trace: Optional[str] = None
) -> float:
    """Evaluate goal decomposition quality.

    Scoring Components:
    - 0.5: Sub-goals align with action taken
    - 0.3: Required info completeness
    - 0.2: Goal actionability

    Args:
        example: Ground truth from BrainDecision
        pred: Model prediction with sub_goals, required_info
        trace: Optional execution trace

    Returns:
        Score between 0.0 and 1.0
    """
    score = 0.0

    # Ground truth
    action_taken = example.get("action_taken")
    state_snapshot = example.get("state_snapshot")

    # Prediction
    pred_goals = pred.sub_goals
    pred_required_info = pred.required_info

    # Component 1: Goal Alignment (0.5 points)
    if action_taken and pred_goals:
        action_lower = action_taken.lower()
        alignment = 0.0

        for goal in pred_goals[:3]:
            goal_lower = goal.lower()
            action_verbs = ["extract", "validate", "schedule", "update", "check"]
            if any(verb in goal_lower and verb in action_lower for verb in action_verbs):
                alignment += 0.2

        score += min(alignment, 0.5)

    # Component 2: Required Info (0.3 points)
    if state_snapshot:
        try:
            state = json.loads(state_snapshot)
            missing = []
            if not state.get("profile_complete"):
                missing.append("profile")
            if not state.get("vehicle_selected"):
                missing.append("vehicle")

            if missing and pred_required_info:
                info_lower = [i.lower() for i in pred_required_info]
                matches = sum(1 for m in missing if any(m in i for i in info_lower))
                score += min(matches * 0.15, 0.3)
        except json.JSONDecodeError:
            pass

    # Component 3: Actionability (0.2 points)
    if pred_goals:
        action_verbs = ["extract", "collect", "validate", "confirm", "schedule"]
        actionable = sum(1 for g in pred_goals if any(v in g.lower() for v in action_verbs))
        if actionable >= len(pred_goals) * 0.7:
            score += 0.2

    return max(min(score, 1.0), 0.0)
