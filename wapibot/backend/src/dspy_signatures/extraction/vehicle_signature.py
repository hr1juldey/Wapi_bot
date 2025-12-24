"""DSPy signature for vehicle details extraction.

Extracts vehicle brand, model, and registration number from conversation.
"""

import dspy


class VehicleExtractionSignature(dspy.Signature):
    """Extract vehicle details from user message.

    Identifies vehicle brand, model, and license plate.
    Handles Indian vehicle brands and formats.
    """

    conversation_history: str = dspy.InputField(
        desc="Previous conversation turns for context"
    )
    user_message: str = dspy.InputField(
        desc="Current user message to extract from"
    )
    context: str = dspy.InputField(
        desc="Extraction context (e.g., 'Collecting vehicle for car wash')"
    )

    brand: str = dspy.OutputField(
        desc="Vehicle brand (e.g., Tata, Honda, Mahindra)"
    )
    model: str = dspy.OutputField(
        desc="Vehicle model (e.g., Nexon, City, Scorpio)"
    )
    number_plate: str = dspy.OutputField(
        desc="License plate number (Indian format: MH12AB1234)"
    )
    confidence: str = dspy.OutputField(
        desc="Extraction confidence: 'low', 'medium', or 'high'"
    )
    reasoning: str = dspy.OutputField(
        desc="Why these vehicle details were extracted"
    )
