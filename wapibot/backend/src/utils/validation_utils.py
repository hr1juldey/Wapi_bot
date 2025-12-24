"""Common validation utilities for data validation.

Provides helpers for validating phone numbers, emails, vehicle brands, etc.
"""

import re
from typing import Optional


# Vehicle brands list (for validation)
VEHICLE_BRANDS = {
    "tata", "mahindra", "maruti", "suzuki", "honda", "toyota", "hyundai",
    "ford", "chevrolet", "nissan", "volkswagen", "bmw", "mercedes", "audi",
    "kia", "mg", "renault", "skoda", "jeep", "fiat"
}


def is_vehicle_brand(name: str) -> bool:
    """Check if string is a known vehicle brand.

    Prevents false positives like "TATA" being extracted as a name
    when it's actually a vehicle brand.

    Args:
        name: String to check

    Returns:
        True if it's a vehicle brand

    Example:
        >>> is_vehicle_brand("TATA")
        True
        >>> is_vehicle_brand("Hrijul")
        False
    """
    if not name:
        return False

    # Check if exact match or part of name
    name_lower = name.lower().strip()
    return any(brand in name_lower for brand in VEHICLE_BRANDS)


def is_valid_indian_phone(phone: str) -> bool:
    """Validate Indian phone number format.

    Args:
        phone: Phone number string

    Returns:
        True if valid Indian format

    Example:
        >>> is_valid_indian_phone("9876543210")
        True
    """
    if not phone:
        return False

    # Clean phone number
    cleaned = re.sub(r'[^\d]', '', phone)

    # Remove +91 prefix if present
    if cleaned.startswith('91') and len(cleaned) == 12:
        cleaned = cleaned[2:]

    # Indian: 10 digits starting with 6-9
    if len(cleaned) == 10 and cleaned[0] in '6789':
        return True

    return False


def is_valid_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email address string

    Returns:
        True if valid email format

    Example:
        >>> is_valid_email("user@example.com")
        True
    """
    if not email:
        return False

    # Basic email regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email.strip()))


def normalize_phone(phone: str) -> Optional[str]:
    """Normalize phone number to 10-digit Indian format.

    Args:
        phone: Phone number string

    Returns:
        Normalized 10-digit phone or None if invalid

    Example:
        >>> normalize_phone("+91 98765 43210")
        "9876543210"
    """
    if not phone:
        return None

    # Clean and remove +91
    cleaned = re.sub(r'[^\d]', '', phone)
    if cleaned.startswith('91') and len(cleaned) == 12:
        cleaned = cleaned[2:]

    # Validate
    if is_valid_indian_phone(cleaned):
        return cleaned

    return None
