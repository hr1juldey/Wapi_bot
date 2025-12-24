"""Utilities for nested field operations on BookingState.

Provides helpers for getting/setting nested fields using dot notation.
Supports the atomic node architecture.
"""

from typing import Any, Optional
from workflows.shared.state import BookingState


def get_nested_field(state: BookingState, field_path: str) -> Any:
    """Get nested field value using dot notation.

    Args:
        state: BookingState to read from
        field_path: Dot-separated path (e.g., "customer.first_name")

    Returns:
        Field value or None if path doesn't exist

    Example:
        >>> get_nested_field(state, "customer.first_name")
        "Hrijul"
    """
    parts = field_path.split(".")
    current = state

    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None

    return current


def set_nested_field(state: BookingState, field_path: str, value: Any) -> None:
    """Set nested field value using dot notation.

    Args:
        state: BookingState to modify
        field_path: Dot-separated path (e.g., "customer.first_name")
        value: Value to set

    Example:
        >>> set_nested_field(state, "customer.first_name", "Hrijul")
    """
    parts = field_path.split(".")
    current = state

    # Navigate to parent
    for part in parts[:-1]:
        if part not in current or current[part] is None:
            current[part] = {}
        current = current[part]

    # Set final field
    current[parts[-1]] = value


def field_exists(state: BookingState, field_path: str) -> bool:
    """Check if nested field exists and is not None.

    Args:
        state: BookingState to check
        field_path: Dot-separated path

    Returns:
        True if field exists and is not None

    Example:
        >>> field_exists(state, "customer.phone")
        True
    """
    value = get_nested_field(state, field_path)
    return value is not None and value != ""


def delete_nested_field(state: BookingState, field_path: str) -> bool:
    """Delete nested field if it exists.

    Args:
        state: BookingState to modify
        field_path: Dot-separated path

    Returns:
        True if field was deleted, False if it didn't exist

    Example:
        >>> delete_nested_field(state, "customer.email")
        True
    """
    parts = field_path.split(".")
    current = state

    # Navigate to parent
    for part in parts[:-1]:
        if not isinstance(current, dict) or part not in current:
            return False
        current = current[part]

    # Delete final field
    if isinstance(current, dict) and parts[-1] in current:
        del current[parts[-1]]
        return True

    return False
