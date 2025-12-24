"""Regex-based email extraction fallback.

Fast email extraction using standard email regex pattern compatible with Pydantic EmailStr.
"""

import re
from typing import Optional, Dict
from pydantic import EmailStr, ValidationError


class RegexEmailExtractor:
    """Fast email extraction using regex with EmailStr validation."""

    # Standard email pattern (RFC 5322 simplified)
    PATTERN = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'

    # Common placeholders to reject
    PLACEHOLDERS = {
        'none@example.com',
        'test@test.com',
        'noreply@example.com',
        'no-reply@example.com',
        'email@example.com',
    }

    def extract(self, message: str) -> Optional[Dict[str, str]]:
        """Extract email address from message.

        Uses regex for extraction and Pydantic EmailStr for validation.

        Args:
            message: User message text

        Returns:
            {"email": "user@example.com"} or None
        """
        if not message:
            return None

        match = re.search(self.PATTERN, message)
        if not match:
            return None

        email_candidate = match.group(0).strip().lower()

        # Reject placeholders
        if email_candidate in self.PLACEHOLDERS:
            return None

        # Validate using Pydantic EmailStr
        try:
            # EmailStr validation ensures RFC 5322 compliance
            validated_email = EmailStr._validate(email_candidate)
            return {"email": str(validated_email)}
        except (ValidationError, ValueError):
            # Invalid email format
            return None