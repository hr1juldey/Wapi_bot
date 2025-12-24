"""Appointment-related domain models.

Provides validated models for date and time slot booking
with comprehensive validation rules.
"""

from datetime import date, timedelta
from typing import Optional
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
    computed_field,
    ConfigDict
)
from models.core import ExtractionMetadata


class Date(BaseModel):
    """Validated date with reasonableness checks."""

    model_config = ConfigDict(extra='forbid')

    date_str: str = Field(
        ...,
        min_length=1,
        max_length=20,
        description="Original date string"
    )
    parsed_date: date = Field(
        ...,
        description="Parsed date object"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        default=1.0,
        description="Parsing confidence"
    )
    metadata: ExtractionMetadata = Field(
        description="Extraction metadata"
    )

    @field_validator('date_str')
    @classmethod
    def validate_date_string(cls, v: str) -> str:
        """Validate date string is not a placeholder."""
        if v.lower().strip() in ['none', 'unknown', 'n/a', 'tbd', 'later']:
            raise ValueError("Date string cannot be placeholder")
        return v.strip()

    @field_validator('parsed_date')
    @classmethod
    def validate_parsed_date(cls, v: date) -> date:
        """Validate parsed date is not in far past or future."""
        today = date.today()
        if v < today.replace(year=today.year - 1):
            raise ValueError(f"Date {v} is too far in the past")
        if v > today.replace(year=today.year + 2):
            raise ValueError(f"Date {v} is too far in the future")
        return v

    @model_validator(mode='after')
    def validate_date_reasonableness(self):
        """Validate date is within reasonable range."""
        today = date.today()
        max_years_ahead = 3
        max_years_back = 10

        future_limit = today.replace(year=today.year + max_years_ahead)
        past_limit = today.replace(year=today.year - max_years_back)

        if self.parsed_date > future_limit:
            raise ValueError(
                f"Date {self.parsed_date} too far in future"
            )
        if self.parsed_date < past_limit:
            raise ValueError(
                f"Date {self.parsed_date} too far in past"
            )

        # Validate calendar date
        try:
            date(
                self.parsed_date.year,
                self.parsed_date.month,
                self.parsed_date.day
            )
        except ValueError as e:
            month = self.parsed_date.month
            day = self.parsed_date.day

            # Lenient validation for LLM quirks
            if month == 2 and day > 29:
                raise ValueError(f"Invalid date: {e}")
            elif month in [4, 6, 9, 11] and day > 30:
                raise ValueError(f"Invalid date: {e}")
            elif day > 31:
                raise ValueError(f"Invalid date: {e}")

        return self

    @computed_field
    @property
    def is_in_past(self) -> bool:
        """Check if date is in the past."""
        return self.parsed_date < date.today()

    @computed_field
    @property
    def days_from_now(self) -> int:
        """Days from today."""
        delta = self.parsed_date - date.today()
        return delta.days


class Appointment(BaseModel):
    """Complete appointment details with dynamic time slots from Yawlit API."""

    model_config = ConfigDict(extra='forbid')

    date: Date = Field(description="Appointment date")
    time_slot: Optional[str] = Field(
        default=None,
        description="Time slot (fetched from Yawlit API)"
    )
    time_slot_id: Optional[str] = Field(
        default=None,
        description="Time slot ID from Yawlit API"
    )
    service_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Type of service"
    )
    metadata: ExtractionMetadata = Field(
        description="Extraction metadata"
    )

    @field_validator('time_slot')
    @classmethod
    def validate_time_slot(cls, v: Optional[str]) -> Optional[str]:
        """Validate time slot format if provided.

        Note: Actual availability should be checked against Yawlit API.
        This just validates the format.
        """
        if v is None:
            return v

        cleaned = v.strip()
        if cleaned.lower() in ['none', 'unknown', 'n/a', 'tbd', '']:
            return None

        return cleaned

    @field_validator('service_type')
    @classmethod
    def validate_service_type(cls, v: str) -> str:
        """Validate service type is not placeholder."""
        cleaned = v.strip().lower()
        if cleaned in ['none', 'unknown', 'n/a', 'tbd', '']:
            raise ValueError("Service type cannot be placeholder")
        if len(cleaned) < 3:
            raise ValueError("Service type too short")
        return v.strip()

    @computed_field
    @property
    def is_same_day(self) -> bool:
        """Check if appointment is today."""
        return self.date.parsed_date == date.today()

    @computed_field
    @property
    def is_next_day(self) -> bool:
        """Check if appointment is tomorrow."""
        tomorrow = date.today() + timedelta(days=1)
        return self.date.parsed_date == tomorrow
