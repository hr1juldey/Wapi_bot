"""Regex-based phone number extraction fallback.

Fast, reliable phone extraction using regex patterns for Indian formats.
"""

import re
from typing import Optional, Dict


class RegexPhoneExtractor:
    """Fast phone extraction using regex patterns."""

    # Indian phone patterns
    PATTERNS = [
        # +91 9876543210
        r'\+91[\s-]?([6789]\d{9})',
        # 91-9876543210 or 919876543210
        r'91[\s-]?([6789]\d{9})',
        # 9876543210 (plain 10-digit)
        r'\b([6789]\d{9})\b',
        # 98765 43210 (with space)
        r'\b([6789]\d{4})[\s-]?(\d{5})\b',
    ]

    def extract(self, message: str) -> Optional[Dict[str, str]]:
        """Extract phone number from message using regex.

        Args:
            message: User message text

        Returns:
            {"phone_number": "9876543210"} or None
        """
        if not message:
            return None

        message = message.strip()

        # Try each pattern
        for pattern in self.PATTERNS:
            match = re.search(pattern, message)
            if match:
                # Extract and clean phone number
                if len(match.groups()) == 2:
                    # Pattern with space (group1 + group2)
                    phone = match.group(1) + match.group(2)
                else:
                    phone = match.group(1)

                # Clean
                phone = re.sub(r'[^\d]', '', phone)

                # Validate length
                if len(phone) == 10 and phone[0] in '6789':
                    return {
                        "phone_number": phone
                    }

        return None
