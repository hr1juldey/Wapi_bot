"""Conflict detection signature - detects user frustration, bargaining, etc."""

import dspy


class ConflictSignature(dspy.Signature):
    """Detect conflicts in user messages (ACC-like function).

    Identifies: frustration, confusion, bargaining, off-topic, cancellation intent.
    """

    conversation_history = dspy.InputField(
        desc="Previous conversation messages"
    )
    user_message = dspy.InputField(
        desc="Current user message to analyze"
    )

    conflict_type = dspy.OutputField(
        desc="Type of conflict: frustration|confusion|bargaining|off_topic|cancellation|none"
    )
    confidence = dspy.OutputField(
        desc="Confidence score 0.0-1.0"
    )
    reasoning = dspy.OutputField(
        desc="Brief explanation of detection"
    )
