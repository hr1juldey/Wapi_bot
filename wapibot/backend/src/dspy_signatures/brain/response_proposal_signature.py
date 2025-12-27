"""Response proposal signature - proposes optimal response."""

import dspy


class ResponseProposalSignature(dspy.Signature):
    """Propose optimal response to user (dlPFC-like function).

    Used with BestOfN + Refine for high-quality responses.
    """

    conversation_history = dspy.InputField(
        desc="Previous conversation messages"
    )
    user_message = dspy.InputField(
        desc="Current user message"
    )
    current_state = dspy.InputField(
        desc="Current booking state (customer, vehicle, service, etc.)"
    )
    detected_conflict = dspy.InputField(
        desc="Any detected conflict (frustration, bargaining, etc.)"
    )

    proposed_response = dspy.OutputField(
        desc="Optimal response message"
    )
    tone = dspy.OutputField(
        desc="Response tone: friendly|professional|empathetic|firm"
    )
    confidence = dspy.OutputField(
        desc="Confidence in this response 0.0-1.0"
    )
    reasoning = dspy.OutputField(
        desc="Why this response is appropriate"
    )
