"""Vehicle details extractor using DSPy Chain of Thought.

Extracts vehicle brand, model, and registration number.
"""

import dspy
from typing import List, Dict, Any

from dspy_signatures.extraction.vehicle_signature import VehicleExtractionSignature
from utils.history_utils import create_dspy_history
from utils.validation_utils import map_confidence_to_float


class VehicleExtractor(dspy.Module):
    """Extract vehicle details using DSPy Chain of Thought."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(VehicleExtractionSignature)

    def __call__(
        self,
        conversation_history: List[Dict[str, str]] = None,
        user_message: str = "",
        context: str = "Collecting vehicle details for service"
    ) -> Dict[str, Any]:
        """Extract vehicle details from user message.

        Args:
            conversation_history: List of {"role": "...", "content": "..."}
            user_message: Current user message
            context: Extraction context

        Returns:
            Dict with brand, model, number_plate, confidence
        """
        if not conversation_history:
            conversation_history = []

        dspy_history = create_dspy_history(conversation_history)

        result = self.predictor(
            conversation_history=dspy_history,
            user_message=user_message,
            context=context
        )

        confidence_str = getattr(result, "confidence", "medium")
        confidence_float = map_confidence_to_float(confidence_str)

        return {
            "brand": getattr(result, "brand", "").strip(),
            "model": getattr(result, "model", "").strip(),
            "number_plate": getattr(result, "number_plate", "").strip(),
            "confidence": confidence_float
        }
