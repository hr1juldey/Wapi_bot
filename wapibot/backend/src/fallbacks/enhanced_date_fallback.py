"""Enhanced date extraction with ordinal and relative date support.

Handles:
- Ordinal dates: "31st", "1st December", "2nd"
- Relative dates: "next Wednesday", "next week"
- Ambiguous date confirmation needed when month not specified
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fallbacks.ordinal_patterns import (
    RELATIVE_DAY_PATTERNS,
    MONTH_NAMES
)


def extract_ordinal_number(text: str) -> Optional[int]:
    """Extract day number from ordinal text (1st → 1, 31st → 31)."""
    pattern = r'\b(\d{1,2})(st|nd|rd|th)\b'
    match = re.search(pattern, text.lower())
    if match:
        return int(match.group(1))
    return None


def extract_enhanced_date(message: str) -> Optional[Dict[str, Any]]:
    """Extract date with ordinal and relative support.

    Returns:
        Dict with:
            - preferred_date: ISO date string
            - confidence: float
            - needs_confirmation: bool
            - confirmation_prompt: Optional[str]
    """
    message_lower = message.lower()
    today = datetime.now().date()

    # Try ordinal with month first (highest confidence)
    ordinal_month_pattern = r'\b(\d{1,2})(st|nd|rd|th)\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b'
    match = re.search(ordinal_month_pattern, message_lower)
    if match:
        day = int(match.group(1))
        month_name = match.group(3)
        month = MONTH_NAMES[month_name]
        year = today.year
        if month < today.month or (month == today.month and day < today.day):
            year += 1  # Next year if date has passed
        target_date = datetime(year, month, day).date()
        return {
            "preferred_date": target_date.isoformat(),
            "confidence": 0.95,
            "needs_confirmation": False
        }

    # Try "next Monday/Tuesday/etc" patterns
    weekdays = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }

    for day_name, pattern in RELATIVE_DAY_PATTERNS.items():
        if "next_" in day_name and day_name != "next_week":
            if re.search(pattern, message_lower):
                weekday_name = day_name.replace("next_", "")
                target_weekday = weekdays[weekday_name]
                current_weekday = today.weekday()
                days_ahead = (target_weekday - current_weekday) % 7
                if days_ahead == 0:
                    days_ahead = 7  # Force next week
                target_date = today + timedelta(days=days_ahead)
                return {
                    "preferred_date": target_date.isoformat(),
                    "confidence": 0.90,
                    "needs_confirmation": False
                }

    # Try ordinal only (needs confirmation - ambiguous)
    day_num = extract_ordinal_number(message_lower)
    if day_num and 1 <= day_num <= 31:
        # Assume current month, or next month if day has passed
        month = today.month
        year = today.year
        if day_num < today.day:
            month += 1
            if month > 12:
                month = 1
                year += 1
        try:
            target_date = datetime(year, month, day_num).date()
            month_name = target_date.strftime("%B")
            return {
                "preferred_date": target_date.isoformat(),
                "confidence": 0.70,
                "needs_confirmation": True,
                "confirmation_prompt": f"Did you mean {month_name} {day_num}?"
            }
        except ValueError:
            return None

    return None