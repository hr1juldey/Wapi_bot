"""Regex-based email extraction fallback.

Fast email extraction using standard email regex pattern.
"""

import re
from typing import Optional, Dict


class RegexEmailExtractor:
    """Fast email extraction using regex."""

    # Standard email pattern
    PATTERN = r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b'

    def extract(self, message: str) -> Optional[Dict[str, str]]:
        """Extract email address from message.

        Args:
            message: User message text

        Returns:
            {"email": "user@example.com"} or None
        """
        if not message:
            return None

        match = re.search(self.PATTERN, message)
        if match:
            email = match.group(0).strip().lower()

            # Validate not a placeholder
            if email not in ['none@example.com', 'test@test.com']:
                return {
                    "email": email
                }

        return None
