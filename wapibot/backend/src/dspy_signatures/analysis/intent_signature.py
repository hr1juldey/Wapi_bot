"""Intent classification signature for user message understanding.

Classifies user intent to route conversation flow appropriately.
"""

import dspy


class IntentClassificationSignature(dspy.Signature):
    """Classify user intent from message."""

    conversation_history: str = dspy.InputField(
        desc="Previous conversation turns for context"
    )
    user_message: str = dspy.InputField(
        desc="Current user message to classify"
    )
    context: str = dspy.InputField(
        desc="Classification context (current conversation state)"
    )

    # Intent categories
    intent: str = dspy.OutputField(
        desc="""Primary intent, one of:
        - 'booking_new': User wants to create new booking
        - 'booking_modify': User wants to change existing booking
        - 'booking_cancel': User wants to cancel booking
        - 'booking_inquiry': User asks about booking details/status
        - 'general_question': General questions about services
        - 'greeting': Greetings/small talk
        - 'complaint': Complaint or negative feedback
        - 'confirmation': User confirming provided information
        - 'correction': User correcting previously provided info
        - 'clarification_needed': User doesn't understand question
        """
    )

    confidence: str = dspy.OutputField(
        desc="Classification confidence: 'low', 'medium', 'high'"
    )

    reasoning: str = dspy.OutputField(
        desc="Why this intent was classified"
    )
