"""Typo detection signature for message correction.

Detects typos and suggests corrections for important fields.
"""

import dspy


class TypoDetectionSignature(dspy.Signature):
    """Detect typos and suggest corrections."""

    user_message: str = dspy.InputField(
        desc="User message to check for typos"
    )
    field_context: str = dspy.InputField(
        desc="Field being extracted (e.g., 'name', 'vehicle_brand', 'email')"
    )
    extracted_value: str = dspy.InputField(
        desc="The value extracted from the message"
    )

    # Typo detection output
    has_typo: str = dspy.OutputField(
        desc="Whether typo detected: 'yes' or 'no'"
    )

    suggested_correction: str = dspy.OutputField(
        desc="Suggested correction if typo detected, otherwise empty string"
    )

    confidence: str = dspy.OutputField(
        desc="Typo detection confidence: 'low', 'medium', 'high'"
    )

    reasoning: str = dspy.OutputField(
        desc="Why typo was detected or why value is correct"
    )
