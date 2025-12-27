"""State evaluation signature for quality assessment."""

import dspy


class StateEvaluationSignature(dspy.Signature):
    """Evaluate conversation quality and booking progress (OFC-like).

    Assesses:
    - Booking completeness (0.0-1.0)
    - User satisfaction (0.0-1.0)
    - Overall conversation quality (0.0-1.0)
    """

    conversation_history: str = dspy.InputField(
        desc="Recent conversation messages (role: content format)"
    )
    booking_state: str = dspy.InputField(
        desc="Current booking progress (profile, vehicle, service, slot status)"
    )

    quality_score: float = dspy.OutputField(
        desc="Overall conversation quality (0.0-1.0)"
    )
    completeness: float = dspy.OutputField(
        desc="Booking completeness percentage (0.0-1.0)"
    )
    user_satisfaction: float = dspy.OutputField(
        desc="Estimated user satisfaction (0.0-1.0)"
    )
    reasoning: str = dspy.OutputField(
        desc="Reasoning for the evaluation scores"
    )
