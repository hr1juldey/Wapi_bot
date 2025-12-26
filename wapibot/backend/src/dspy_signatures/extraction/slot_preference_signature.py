"""DSPy signature for slot preference extraction.

Extracts date and time range preferences for appointment booking.
"""

import dspy


class SlotPreferenceSignature(dspy.Signature):
    """Extract date and time preferences from user message.

    Identifies when the customer wants to book (date + time of day).
    Supports multilingual inputs (English, Hindi, Bengali, Hinglish, Benglish).
    """

    conversation_history: str = dspy.InputField(
        desc="Previous conversation turns for context"
    )
    user_message: str = dspy.InputField(
        desc="Current user message to extract preference from"
    )
    context: str = dspy.InputField(
        desc="Extraction context (e.g., 'Asking when to book appointment')"
    )

    preferred_date: str = dspy.OutputField(
        desc="Preferred date in YYYY-MM-DD format or relative (e.g., 'tomorrow', 'next Monday', 'today'). Empty if not specified."
    )
    preferred_time_range: str = dspy.OutputField(
        desc="Preferred time of day: 'morning', 'afternoon', or 'evening'. Empty if not specified."
    )
    confidence: str = dspy.OutputField(
        desc="Extraction confidence: 'low', 'medium', or 'high'"
    )
    reasoning: str = dspy.OutputField(
        desc="Why these preferences were extracted, especially for multilingual inputs"
    )
