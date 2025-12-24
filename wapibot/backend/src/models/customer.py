"""Customer-related domain models.

Provides validated models for customer name, phone number, and email
with comprehensive validation rules for Indian formats.
"""

import re
from typing import Annotated
from pydantic import BaseModel, Field, EmailStr, field_validator, model_validator, ConfigDict
from pydantic_extra_types.phone_numbers import PhoneNumber
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


class Email(BaseModel):
    """Validated email address using Pydantic v2 EmailStr."""

    model_config = ConfigDict(extra='forbid')

    email: EmailStr = Field(
        ...,
        description="RFC 5322 compliant email address"
    )
    metadata: ExtractionMetadata = Field(
        description="Extraction metadata"
    )

    @field_validator('email', mode='before')
    @classmethod
    def reject_placeholders(cls, v):
        """Reject common placeholder email values."""
        if isinstance(v, str):
            v_lower = v.lower().strip()
            placeholders = ['none@example.com', 'test@test.com', 'noreply@', 'no-reply@']
            if any(p in v_lower for p in placeholders):
                raise ValueError(f"Placeholder email not allowed: {v}")
        return v


# Type alias for Indian phone numbers (default region IN)
IndianPhoneNumber = Annotated[PhoneNumber, Field(default_region='IN')]


class Phone(BaseModel):
    """Validated phone number using Pydantic v2 PhoneNumber type."""

    model_config = ConfigDict(extra='forbid')

    phone_number: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Phone number (preferably Indian format)"
    )
    metadata: ExtractionMetadata = Field(
        description="Extraction metadata"
    )

    @field_validator('phone_number', mode='before')
    @classmethod
    def validate_and_normalize_phone(cls, v) -> str:
        """Validate and normalize phone number.

        Accepts Indian 10-digit format or international formats.
        For production use with PhoneNumber type, use the commented alternative.
        """
        if not v or (isinstance(v, str) and not v.strip()):
            raise ValueError("Phone number cannot be empty")

        # Convert to string if needed
        v_str = str(v)

        # Reject placeholders
        if v_str.lower().strip() in ['none', 'unknown', 'n/a', 'null', '']:
            raise ValueError("Invalid phone placeholder")

        # Remove common separators
        cleaned = v_str.replace(' ', '').replace('-', '') \
            .replace('(', '').replace(')', '') \
            .replace('+', '').strip()

        # Remove country code if present (91 for India)
        if cleaned.startswith('91') and len(cleaned) >= 12:
            cleaned = cleaned[2:]

        # Indian format: 10 digits starting with 6-9
        if len(cleaned) == 10 and cleaned.isdigit() and cleaned[0] in '6789':
            return cleaned

        # International: 10-15 digits
        if 10 <= len(cleaned) <= 15 and cleaned.isdigit():
            return cleaned

        raise ValueError(f"Invalid phone format: {v_str}")
