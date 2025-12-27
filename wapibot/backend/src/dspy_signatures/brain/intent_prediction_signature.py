"""Intent prediction signature - predicts user's next action."""

import dspy


class IntentPredictionSignature(dspy.Signature):
    """Predict user's next intent (OFC-like function).

    Predicts what user will likely do next in conversation.
    """

    conversation_history = dspy.InputField(
        desc="Previous conversation messages"
    )
    current_state = dspy.InputField(
        desc="Current booking state (customer, vehicle, service, etc.)"
    )
    user_message = dspy.InputField(
        desc="Latest user message"
    )

    predicted_intent = dspy.OutputField(
        desc="Predicted next action: continue|cancel|question|bargain|clarify"
    )
    confidence = dspy.OutputField(
        desc="Confidence score 0.0-1.0"
    )
