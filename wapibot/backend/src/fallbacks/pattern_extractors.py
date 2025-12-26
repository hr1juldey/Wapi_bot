"""Pattern-based extractor functions for fallback extraction.

Implements the extraction logic for different pattern types (time range, date, etc.).
Used by nodes/atomic/fallback_extract.py atomic node.
"""

import re
from datetime import datetime, timedelta
from typing import List, Any, Optional, Dict


def extract_time_range(message: str, patterns: List[Any]) -> Optional[Dict[str, Any]]:
    """Extract time range (morning/afternoon/evening) from message.

    Args:
        message: User message to extract from
        patterns: List of TimeRangePattern configurations

    Returns:
        Dict with preferred_time_range, start_hour, end_hour, confidence
    """
    message_lower = message.lower()

    for pattern_config in patterns:
        for pattern in pattern_config.patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return {
                    "preferred_time_range": pattern_config.range_name,
                    "start_hour": pattern_config.start_hour,
                    "end_hour": pattern_config.end_hour,
                    "confidence": 0.95
                }
    return None


def extract_date(message: str, patterns: List[Any]) -> Optional[Dict[str, Any]]:
    """Extract date from message (today/tomorrow/weekdays).

    Args:
        message: User message to extract from
        patterns: List of DatePattern configurations

    Returns:
        Dict with preferred_date (ISO format), date_str, confidence
    """
    message_lower = message.lower()
    today = datetime.now().date()

    # Try simple date patterns first (today/tomorrow)
    for pattern_config in patterns:
        if not pattern_config.requires_weekday:
            for pattern in pattern_config.regex_patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    target_date = today + timedelta(days=pattern_config.day_offset)
                    return {
                        "preferred_date": target_date.isoformat(),
                        "date_str": pattern_config.pattern_name,
                        "confidence": 0.95
                    }

    # Try weekday patterns (Monday, Tuesday, etc.)
    from models.extraction_patterns import WEEKDAY_PATTERNS
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }

    for day_name, day_patterns in WEEKDAY_PATTERNS.items():
        for pattern in day_patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                target_weekday = weekdays[day_name]
                current_weekday = today.weekday()
                days_ahead = (target_weekday - current_weekday) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Next week if same day
                target_date = today + timedelta(days=days_ahead)
                return {
                    "preferred_date": target_date.isoformat(),
                    "date_str": day_name,
                    "confidence": 0.90
                }

    return None
