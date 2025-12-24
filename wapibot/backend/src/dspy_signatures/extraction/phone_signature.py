"""DSPy signature for phone number extraction.

Extracts Indian phone numbers from conversation with confidence scoring.
"""

import dspy


class PhoneExtractionSignature(dspy.Signature):
    """Extract phone number from user message.

    Focuses on Indian 10-digit format and international formats.
    Returns confidence based on format validity.
    """

    conversation_history: str = dspy.InputField(
        desc="Previous conversation turns for context"
    )
    user_message: str = dspy.InputField(
        desc="Current user message to extract from"
    )
    context: str = dspy.InputField(
        desc="Extraction context (e.g., 'Collecting contact for booking')"
    )

    phone_number: str = dspy.OutputField(
        desc="Extracted 10-digit phone number (Indian format preferred)"
    )
    confidence: str = dspy.OutputField(
        desc="Extraction confidence: 'low', 'medium', or 'high'"
    )
    reasoning: str = dspy.OutputField(
        desc="Why this phone number was extracted and confidence level"
    )
