"""Regex-based date extraction fallback.

Fast relative date parsing (tomorrow, next Monday, etc).
"""

import re
from datetime import date, timedelta
from typing import Optional, Dict


class RegexDateExtractor:
    """Fast date extraction using regex for common patterns."""

    def extract(self, message: str) -> Optional[Dict[str, str]]:
        """Extract date from message using common patterns.

        Args:
            message: User message text

        Returns:
            {"date_str": "tomorrow", "parsed_date": "2025-12-25"} or None
        """
        if not message:
            return None

        message_lower = message.lower()
        today = date.today()

        # Today
        if re.search(r'\b(today|aaj)\b', message_lower):
            return {
                "date_str": "today",
                "parsed_date": today.isoformat()
            }

        # Tomorrow
        if re.search(r'\b(tomorrow|kal)\b', message_lower):
            tomorrow = today + timedelta(days=1)
            return {
                "date_str": "tomorrow",
                "parsed_date": tomorrow.isoformat()
            }

        # Day after tomorrow
        if re.search(r'\bday after tomorrow\b', message_lower):
            day_after = today + timedelta(days=2)
            return {
                "date_str": "day after tomorrow",
                "parsed_date": day_after.isoformat()
            }

        # Next Monday, Tuesday, etc.
        weekdays = {
            "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
            "friday": 4, "saturday": 5, "sunday": 6
        }

        for day_name, day_num in weekdays.items():
            if re.search(rf'\bnext {day_name}\b', message_lower):
                # Calculate next occurrence of this weekday
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:  # Target day already passed this week
                    days_ahead += 7
                next_day = today + timedelta(days=days_ahead)

                return {
                    "date_str": f"next {day_name}",
                    "parsed_date": next_day.isoformat()
                }

        return None
