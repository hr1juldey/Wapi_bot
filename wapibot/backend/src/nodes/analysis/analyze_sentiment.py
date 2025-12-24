"""Sentiment analysis node using DSPy analyzer.

Analyzes user message sentiment across 5 dimensions.
"""

from typing import Dict, Any, List

from dspy_modules.analyzers.sentiment_analyzer import SentimentAnalyzer
from models.booking_state import BookingState


class AnalyzeSentimentNode:
    """Analyze sentiment in user message."""

    def __init__(self):
        """Initialize sentiment analyzer."""
        self.analyzer = SentimentAnalyzer()

    def __call__(
        self,
        state: BookingState,
        conversation_history: List[Dict[str, str]],
        user_message: str,
        context: str = "Analyzing customer sentiment"
    ) -> Dict[str, Any]:
        """Analyze sentiment across 5 dimensions.

        Args:
            state: Current booking state
            conversation_history: Previous conversation turns
            user_message: Current user message
            context: Analysis context

        Returns:
            Dict with sentiment analysis results
        """
        if not user_message:
            return {
                "politeness": "neutral",
                "urgency": "none",
                "frustration": "none",
                "clarity": "clear",
                "engagement": "neutral",
                "overall_sentiment": "neutral",
                "reasoning": "No message to analyze"
            }

        # Call DSPy analyzer
        result = self.analyzer(
            conversation_history=conversation_history,
            user_message=user_message,
            context=context
        )

        return result


# Singleton instance
analyze_sentiment = AnalyzeSentimentNode()
