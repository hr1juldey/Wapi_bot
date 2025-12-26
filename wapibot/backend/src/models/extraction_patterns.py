"""Regex pattern configurations for fallback extraction.

Consolidates all regex patterns for date, time, and preference extraction
in one place. Used by general-purpose fallback extraction atomic node.
"""

from typing import List, Dict
from pydantic import BaseModel, Field


class TimeRangePattern(BaseModel):
    """Time range pattern configuration with multilingual support."""

    range_name: str = Field(description="Time range name (morning/afternoon/evening)")
    patterns: List[str] = Field(description="Regex patterns to match")
    start_hour: int = Field(ge=0, le=23, description="Start hour (24h format)")
    end_hour: int = Field(ge=0, le=23, description="End hour (24h format)")


class DatePattern(BaseModel):
    """Date pattern configuration with multilingual support."""

    pattern_name: str = Field(description="Pattern name (today/tomorrow/weekday)")
    regex_patterns: List[str] = Field(description="Regex patterns to match")
    day_offset: int = Field(description="Days from today (0=today, 1=tomorrow, etc)")
    requires_weekday: bool = Field(
        default=False,
        description="Whether pattern requires weekday calculation"
    )
    weekday_name: str = Field(
        default="",
        description="Weekday name for weekday-based patterns"
    )


# Time Range Configurations (Morning/Afternoon/Evening)
# Supports: English, Hindi, Bengali, Hinglish, Benglish
TIME_RANGE_PATTERNS: List[TimeRangePattern] = [
    TimeRangePattern(
        range_name="morning",
        patterns=[
            r'\b(morning|subah|saver|savere|shokal|sokal|bhor)\b',
            r'\b([6-9]|10|11)\s*am\b',
            r'\b0?[6-9][:]\d{2}\b',  # 6:00, 7:30, etc.
        ],
        start_hour=6,
        end_hour=12
    ),
    TimeRangePattern(
        range_name="afternoon",
        patterns=[
            r'\b(afternoon|dopahar|dophar|lunch|lunchtime|dupur|bikel|bela)\b',
            r'\b(12|1|2|3|4)\s*pm\b',
            r'\b1[2-4][:]\d{2}\b',  # 12:00, 13:30, etc.
        ],
        start_hour=12,
        end_hour=17
    ),
    TimeRangePattern(
        range_name="evening",
        patterns=[
            r'\b(evening|sham|shaam|night|sandhya|sandhye|sondha|bikal|raat|rat)\b',
            r'\b([5-9]|10)\s*pm\b',
            r'\b1[7-9][:]\d{2}\b',  # 17:00, 18:30, etc.
            r'\b20[:]\d{2}\b',      # 20:00, 20:30
        ],
        start_hour=17,
        end_hour=21
    ),
]


# Date Configurations (Today/Tomorrow/Weekdays/Weekend)
# Supports: English, Hindi, Bengali, Hinglish, Benglish
DATE_PATTERNS: List[DatePattern] = [
    DatePattern(
        pattern_name="today",
        regex_patterns=[r'\b(today|aaj|aaj)\b'],
        day_offset=0
    ),
    DatePattern(
        pattern_name="tomorrow",
        regex_patterns=[r'\b(tomorrow|kal|agle din)\b'],
        day_offset=1
    ),
    DatePattern(
        pattern_name="weekend",
        regex_patterns=[
            r'\b(weekend|saturday|sunday|shanibar|robibar|shonbar)\b',
            r'\b(sat|sun)\b'
        ],
        day_offset=0,  # Calculated dynamically
        requires_weekday=True,
        weekday_name="saturday"
    ),
]


# Weekday names for dynamic date calculation
WEEKDAY_PATTERNS: Dict[str, List[str]] = {
    "monday": [r'\b(monday|sombar|somvar)\b', r'\bmon\b'],
    "tuesday": [r'\b(tuesday|mangalbar|mangalvar)\b', r'\btue\b'],
    "wednesday": [r'\b(wednesday|budhbar|budhvar)\b', r'\bwed\b'],
    "thursday": [r'\b(thursday|brihospotibar|guruvar)\b', r'\bthu\b'],
    "friday": [r'\b(friday|shukrobar|shukravar)\b', r'\bfri\b'],
    "saturday": [r'\b(saturday|shonibar|shanivar)\b', r'\bsat\b'],
    "sunday": [r'\b(sunday|robibar|ravivar)\b', r'\bsun\b'],
}
