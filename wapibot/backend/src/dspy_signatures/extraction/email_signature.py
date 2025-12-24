"""DSPy signature for email address extraction.

Extracts email addresses from conversation with format validation.
"""

import dspy


class EmailExtractionSignature(dspy.Signature):
    """Extract email address from user message.

    Validates email format and returns confidence based on validity.
    """

    conversation_history: str = dspy.InputField(
        desc="Previous conversation turns for context"
    )
    user_message: str = dspy.InputField(
        desc="Current user message to extract from"
    )
    context: str = dspy.InputField(
        desc="Extraction context (e.g., 'Collecting contact information')"
    )

    email: str = dspy.OutputField(
        desc="Extracted email address"
    )
    confidence: str = dspy.OutputField(
        desc="Extraction confidence: 'low', 'medium', or 'high'"
    )
    reasoning: str = dspy.OutputField(
        desc="Why this email was extracted and confidence level"
    )
