"""Ordinal date pattern configurations for enhanced date parsing.

Handles dates like "31st", "1st December", "next Wednesday", etc.
Extends existing date pattern system with more sophisticated patterns.
"""

from typing import List, Dict
from pydantic import BaseModel, Field


class OrdinalDatePattern(BaseModel):
    """Ordinal date pattern configuration."""

    pattern_type: str = Field(description="Pattern type (ordinal/month_name/relative)")
    regex: str = Field(description="Regex pattern to match")
    requires_confirmation: bool = Field(
        default=False,
        description="Whether this pattern needs user confirmation"
    )


# Ordinal number patterns (1st, 2nd, 3rd, ..., 31st)
ORDINAL_PATTERNS: List[OrdinalDatePattern] = [
    OrdinalDatePattern(
        pattern_type="ordinal_only",
        regex=r'\b(1st|2nd|3rd|[4-9]th|1[0-9]th|2[0-9]th|3[01]st|3[01]nd|3[01]rd)\b',
        requires_confirmation=True  # Ambiguous without month
    ),
    OrdinalDatePattern(
        pattern_type="ordinal_with_month",
        regex=r'\b(1st|2nd|3rd|[4-9]th|1[0-9]th|2[0-9]th|3[01]st) (january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b',
        requires_confirmation=False
    ),
]

# "next" relative patterns
RELATIVE_DAY_PATTERNS: Dict[str, str] = {
    "next_monday": r'\b(next monday)\b',
    "next_tuesday": r'\b(next tuesday)\b',
    "next_wednesday": r'\b(next wednesday)\b',
    "next_thursday": r'\b(next thursday)\b',
    "next_friday": r'\b(next friday)\b',
    "next_saturday": r'\b(next saturday)\b',
    "next_sunday": r'\b(next sunday)\b',
    "next_week": r'\b(next week)\b',
}

# Month name to number mapping
MONTH_NAMES: Dict[str, int] = {
    "january": 1, "jan": 1,
    "february": 2, "feb": 2,
    "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "may": 5,
    "june": 6, "jun": 6,
    "july": 7, "jul": 7,
    "august": 8, "aug": 8,
    "september": 9, "sep": 9,
    "october": 10, "oct": 10,
    "november": 11, "nov": 11,
    "december": 12, "dec": 12,
}