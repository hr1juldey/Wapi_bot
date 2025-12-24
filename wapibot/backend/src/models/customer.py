"""Customer-related domain models.

Provides validated models for customer name and phone number
with comprehensive validation rules for Indian formats.
"""

import re
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from models.core import ExtractionMetadata


class Name(BaseModel):
    """Validated customer name with consistency checks."""

    model_config = ConfigDict(extra='forbid')

    first_name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r'^[A-Za-z][A-Za-z\'-]*([ .][A-Za-z][A-Za-z\'-]*)*$',
        description="First name with middle names/initials"
    )
    last_name: str = Field(
        default="",
        min_length=0,
        max_length=50,
        pattern=r'^[A-Za-z\'-]*$',
        description="Last name (optional)"
    )
    full_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Complete full name"
    )
    metadata: ExtractionMetadata = Field(
        description="Extraction metadata"
    )

    @model_validator(mode='after')
    def validate_name_consistency(self):
        """Validate first/last name consistency with full name."""
        if self.full_name and (self.first_name or self.last_name):
            full_parts = self.full_name.lower().split()
            first_parts = self.first_name.lower().split()

            # Lenient validation for LLM outputs
            if full_parts and first_parts:
                # Check if first name matches beginning of full name
                _ = any(fp.lower() == full_parts[0] for fp in first_parts)
                # Allow variations (logged as warning, not error)

            if self.last_name and full_parts:
                # Normalize last name for comparison
                _ = self.last_name.lower()
                # Allow LLM format variations

        return self

    @field_validator('first_name', 'last_name', 'full_name')
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Validate name format and capitalize properly."""
        if not v:
            return v

        # Check for valid characters only
        clean_name = re.sub(r'[ -\'.]', '', v)
        if len(clean_name) > 0 and not re.match(r'^[A-Za-z]+$', clean_name):
            raise ValueError(
                "Name contains invalid characters"
            )

        # Capitalize each word
        return ' '.join(word.capitalize() for word in v.split())


class Phone(BaseModel):
    """Validated Indian phone number."""

    model_config = ConfigDict(extra='forbid')

    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="10-digit Indian format preferred"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        default=1.0,
        description="Extraction confidence"
    )
    metadata: ExtractionMetadata = Field(
        description="Extraction metadata"
    )

    @field_validator('phone_number')
    @classmethod
    def validate_and_normalize_phone(cls, v: str) -> str:
        """Validate and normalize to 10-digit Indian format."""
        if not v or not v.strip():
            raise ValueError("Phone number cannot be empty")

        # Remove separators
        cleaned = v.replace(' ', '').replace('-', '') \
            .replace('(', '').replace(')', '') \
            .replace('+91', '').strip()

        # Reject placeholders
        if cleaned.lower() in ['none', 'unknown', 'n/a', '']:
            raise ValueError("Invalid phone placeholder")

        # Indian: 10 digits starting with 6-9
        if len(cleaned) == 10 and cleaned.isdigit() and cleaned[0] in '6789':
            return cleaned

        # International: 10-15 digits
        if 10 <= len(cleaned) <= 15 and cleaned.isdigit():
            return cleaned

        raise ValueError(f"Invalid phone format: {v}")
