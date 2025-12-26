"""Regex-based time range extraction fallback.

Extracts time-of-day preferences (morning/afternoon/evening) from user messages
using pattern matching. Supports English, Hindi, Bengali, Hinglish, and Benglish.
"""

import re
from typing import Optional, Dict, Any


class RegexTimeRangeExtractor:
    """Extract time-of-day preference using regex patterns."""

    TIME_RANGES = {
        "morning": {
            "patterns": [
                # English, Hindi, Bengali
                r'\b(morning|subah|saver|savere|shokal|sokal|bhor)\b',
                r'\b([6-9]|10|11)\s*am\b',
                r'\b0?[6-9][:]\d{2}\b',  # 6:00, 7:30, etc.
            ],
            "start_hour": 6,
            "end_hour": 12
        },
        "afternoon": {
            "patterns": [
                # English, Hindi, Bengali
                r'\b(afternoon|dopahar|dophar|lunch|lunchtime|dupur|bikel|bela)\b',
                r'\b(12|1|2|3|4)\s*pm\b',
                r'\b1[2-4][:]\d{2}\b',  # 12:00, 13:30, etc.
            ],
            "start_hour": 12,
            "end_hour": 17
        },
        "evening": {
            "patterns": [
                # English, Hindi, Bengali
                r'\b(evening|sham|shaam|night|sandhya|sandhye|sondha|bikal|raat|rat)\b',
                r'\b([5-9]|10)\s*pm\b',
                r'\b1[7-9][:]\d{2}\b',  # 17:00, 18:30, etc.
                r'\b20[:]\d{2}\b',      # 20:00, 20:30
            ],
            "start_hour": 17,
            "end_hour": 21
        }
    }

    def extract(self, message: str) -> Optional[Dict[str, Any]]:
        """Extract time range from message.

        Args:
            message: User message to extract time preference from

        Returns:
            Dict with time_range, start_hour, end_hour if found, None otherwise
        """
        if not message:
            return None

        message_lower = message.lower()

        for time_range, config in self.TIME_RANGES.items():
            for pattern in config["patterns"]:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return {
                        "time_range": time_range,
                        "start_hour": config["start_hour"],
                        "end_hour": config["end_hour"]
                    }

        return None
