"""Unit tests for utility functions.

Tests validation_utils and history_utils.
"""

from utils.validation_utils import map_confidence_to_float
from utils.history_utils import create_dspy_history
from core.config import settings


class TestMapConfidenceToFloat:
    """Test confidence mapping utility."""

    def test_high_confidence_mapping(self):
        """Test mapping of 'high' confidence."""
        result = map_confidence_to_float("high")
        assert result == settings.confidence_high
        assert result == 0.9

    def test_medium_confidence_mapping(self):
        """Test mapping of 'medium' confidence."""
        result = map_confidence_to_float("medium")
        assert result == settings.confidence_medium
        assert result == 0.7

    def test_low_confidence_mapping(self):
        """Test mapping of 'low' confidence."""
        result = map_confidence_to_float("low")
        assert result == settings.confidence_low
        assert result == 0.5

    def test_case_insensitive_mapping(self):
        """Test that mapping is case-insensitive."""
        assert map_confidence_to_float("HIGH") == settings.confidence_high
        assert map_confidence_to_float("Medium") == settings.confidence_medium
        assert map_confidence_to_float("LoW") == settings.confidence_low

    def test_unknown_confidence_defaults_to_medium(self):
        """Test that unknown confidence strings default to medium."""
        result = map_confidence_to_float("unknown")
        assert result == settings.confidence_medium

        result = map_confidence_to_float("very_high")
        assert result == settings.confidence_medium


class TestCreateDSpyHistory:
    """Test DSPy history formatting utility."""

    def test_empty_history(self):
        """Test with empty conversation history."""
        result = create_dspy_history([])
        assert isinstance(result, type(create_dspy_history([])))
        assert result.messages == []

    def test_none_history(self):
        """Test with None as history."""
        result = create_dspy_history(None)
        assert isinstance(result, type(create_dspy_history([])))
        assert result.messages == []

    def test_single_turn_history(self):
        """Test with single conversation turn."""
        history = [
            {"role": "user", "content": "Hello"}
        ]
        result = create_dspy_history(history)

        assert len(result.messages) == 1
        assert result.messages[0]["role"] == "user"
        assert result.messages[0]["content"] == "Hello"

    def test_multi_turn_history(self):
        """Test with multiple conversation turns."""
        history = [
            {"role": "user", "content": "Hi there"},
            {"role": "assistant", "content": "Hello! How can I help?"},
            {"role": "user", "content": "I need a car wash"},
        ]
        result = create_dspy_history(history)

        assert len(result.messages) == 3
        assert result.messages[0]["content"] == "Hi there"
        assert result.messages[1]["content"] == "Hello! How can I help?"
        assert result.messages[2]["content"] == "I need a car wash"

    def test_history_order_preserved(self):
        """Test that conversation order is preserved."""
        history = [
            {"role": "user", "content": "First"},
            {"role": "assistant", "content": "Second"},
            {"role": "user", "content": "Third"},
        ]
        result = create_dspy_history(history)

        assert len(result.messages) == 3
        assert result.messages[0]["content"] == "First"
        assert result.messages[1]["content"] == "Second"
        assert result.messages[2]["content"] == "Third"

    def test_role_preservation(self):
        """Test that roles are preserved correctly."""
        history = [
            {"role": "user", "content": "Test"}
        ]
        result = create_dspy_history(history)

        assert result.messages[0]["role"] == "user"

    def test_multiline_content(self):
        """Test handling of multiline content."""
        history = [
            {"role": "user", "content": "Line 1\nLine 2\nLine 3"}
        ]
        result = create_dspy_history(history)

        assert "Line 1\nLine 2\nLine 3" in result.messages[0]["content"]

    def test_special_characters_in_content(self):
        """Test handling of special characters."""
        history = [
            {"role": "user", "content": "Email: test@example.com, Phone: +919876543210"}
        ]
        result = create_dspy_history(history)

        assert "test@example.com" in result.messages[0]["content"]
        assert "+919876543210" in result.messages[0]["content"]

    def test_empty_content_handling(self):
        """Test handling of empty content."""
        history = [
            {"role": "user", "content": ""},
            {"role": "assistant", "content": "Response"},
        ]
        result = create_dspy_history(history)

        assert len(result.messages) == 2
        assert result.messages[0]["content"] == ""
        assert result.messages[1]["content"] == "Response"
