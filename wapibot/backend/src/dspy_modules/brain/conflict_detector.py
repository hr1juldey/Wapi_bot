"""Conflict detector module - ACC-like function (Anterior Cingulate Cortex)."""

import logging
from typing import List, Dict, Any
import dspy
from dspy_signatures.brain.conflict_signature import ConflictSignature

logger = logging.getLogger(__name__)


class ConflictDetector(dspy.Module):
    """Detects conflicts in user messages using ChainOfThought reasoning.

    Conflict types:
    - frustration: User is frustrated or angry
    - confusion: User doesn't understand
    - bargaining: User wants price reduction
    - off_topic: User asking unrelated questions
    - cancellation: User wants to cancel booking
    - none: No conflict detected
    """

    def __init__(self):
        """Initialize conflict detector with ChainOfThought."""
        super().__init__()
        self.detector = dspy.ChainOfThought(ConflictSignature)

    def forward(
        self,
        conversation_history: List[Dict[str, str]],
        user_message: str
    ) -> Dict[str, Any]:
        """Detect conflict in user message.

        Args:
            conversation_history: Previous messages [{role, content}]
            user_message: Current user message

        Returns:
            Dict with conflict_type, confidence, reasoning
        """
        try:
            # Format history for signature
            history_str = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in conversation_history[-5:]  # Last 5 messages
            ])

            # Run ChainOfThought reasoning
            result = self.detector(
                conversation_history=history_str,
                user_message=user_message
            )

            return {
                "conflict_type": result.conflict_type.strip().lower(),
                "confidence": result.confidence,
                "reasoning": result.reasoning
            }

        except Exception as e:
            logger.error(f"Conflict detection failed: {e}")
            return {
                "conflict_type": "none",
                "confidence": 0.0,
                "reasoning": f"Error: {str(e)}"
            }
