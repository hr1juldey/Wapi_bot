"""Sentiment analysis signature for multi-dimensional emotion detection.

Analyzes user messages across 5 dimensions to understand emotional state.
"""

import dspy


class SentimentAnalysisSignature(dspy.Signature):
    """Analyze sentiment across 5 dimensions."""

    conversation_history: str = dspy.InputField(
        desc="Previous conversation turns for context"
    )
    user_message: str = dspy.InputField(
        desc="Current user message to analyze"
    )
    context: str = dspy.InputField(
        desc="Analysis context (e.g., 'booking flow', 'complaint handling')"
    )

    # 5-dimensional sentiment output
    politeness: str = dspy.OutputField(
        desc="Politeness level: 'very_polite', 'polite', 'neutral', 'impolite', 'rude'"
    )
    urgency: str = dspy.OutputField(
        desc="Urgency level: 'urgent', 'moderate', 'low', 'none'"
    )
    frustration: str = dspy.OutputField(
        desc="Frustration level: 'high', 'moderate', 'low', 'none'"
    )
    clarity: str = dspy.OutputField(
        desc="Message clarity: 'very_clear', 'clear', 'somewhat_unclear', 'very_unclear'"
    )
    engagement: str = dspy.OutputField(
        desc="Engagement level: 'very_engaged', 'engaged', 'neutral', 'disengaged'"
    )

    overall_sentiment: str = dspy.OutputField(
        desc="Overall sentiment: 'positive', 'neutral', 'negative'"
    )
    reasoning: str = dspy.OutputField(
        desc="Reasoning for sentiment analysis"
    )
