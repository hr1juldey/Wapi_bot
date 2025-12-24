"""Sentiment analyzer using DSPy Chain of Thought.

Analyzes user messages across 5 emotional dimensions.
"""

import dspy
from typing import List, Dict, Any

from dspy_signatures.analysis.sentiment_signature import SentimentAnalysisSignature
from utils.history_utils import create_dspy_history
from core.config import settings


class SentimentAnalyzer(dspy.Module):
    """Analyze sentiment using DSPy Chain of Thought."""

    def __init__(self):
        super().__init__()
        self.predictor = dspy.ChainOfThought(SentimentAnalysisSignature)

    def __call__(
        self,
        conversation_history: List[Dict[str, str]] = None,
        user_message: str = "",
        context: str = "Analyzing customer sentiment in booking flow"
    ) -> Dict[str, Any]:
        """Analyze sentiment across 5 dimensions.

        Args:
            conversation_history: List of {"role": "...", "content": "..."}
            user_message: Current user message
            context: Analysis context

        Returns:
            Dict with politeness, urgency, frustration, clarity, engagement, overall_sentiment
        """
        if not conversation_history:
            conversation_history = []

        dspy_history = create_dspy_history(conversation_history)

        result = self.predictor(
            conversation_history=dspy_history,
            user_message=user_message,
            context=context
        )

        return {
            "politeness": getattr(result, "politeness", "neutral").lower(),
            "urgency": getattr(result, "urgency", "none").lower(),
            "frustration": getattr(result, "frustration", "none").lower(),
            "clarity": getattr(result, "clarity", "clear").lower(),
            "engagement": getattr(result, "engagement", "neutral").lower(),
            "overall_sentiment": getattr(result, "overall_sentiment", "neutral").lower(),
            "reasoning": getattr(result, "reasoning", "")
        }
