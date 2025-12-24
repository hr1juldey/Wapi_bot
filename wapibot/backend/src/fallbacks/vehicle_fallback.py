"""Regex-based vehicle extraction fallback.

Fast vehicle brand and number plate detection using regex patterns.
"""

import re
from typing import Optional, Dict
from models.vehicle import INDIAN_STATE_CODES, VEHICLE_BRANDS


class RegexVehicleExtractor:
    """Fast vehicle brand and number plate extraction using regex."""

    # Indian license plate patterns
    # Standard: XX00XX0000 (e.g., WB06AF1234)
    STANDARD_PLATE_PATTERN = r'\b([A-Z]{2})[\s\-]?(\d{2})[\s\-]?([A-Z]{1,2})[\s\-]?(\d{4})\b'

    # BH series: 00XX0000XX (e.g., 22BH1234AB)
    BH_PLATE_PATTERN = r'\b\d{2}[\s\-]?BH[\s\-]?\d{4}[\s\-]?[A-Z]{2}\b'

    def extract(self, message: str) -> Optional[Dict[str, str]]:
        """Extract vehicle brand and/or number plate from message.

        Args:
            message: User message text

        Returns:
            {"brand": "Honda", "number_plate": "WB06AF1234"} or None
        """
        if not message:
            return None

        result = {}
        message_upper = message.upper()
        message_lower = message.lower()

        # Extract number plate
        number_plate = self._extract_number_plate(message_upper)
        if number_plate:
            result["number_plate"] = number_plate

        # Extract brand
        brand = self._extract_brand(message_lower)
        if brand:
            result["brand"] = brand

        return result if result else None

    def _extract_number_plate(self, message: str) -> Optional[str]:
        """Extract and normalize Indian license plate.

        Args:
            message: Message text (uppercase)

        Returns:
            Normalized plate (e.g., "WB06AF1234") or None
        """
        # Try BH series format FIRST (more specific)
        match = re.search(self.BH_PLATE_PATTERN, message)
        if match:
            plate = match.group(0)
            # Normalize: remove spaces and hyphens
            return plate.replace(' ', '').replace('-', '')

        # Try standard format and validate state code
        match = re.search(self.STANDARD_PLATE_PATTERN, message)
        if match:
            state_code = match.group(1)
            # Only return if valid Indian state/UT code
            if state_code in INDIAN_STATE_CODES:
                plate = match.group(0)
                # Normalize: remove spaces and hyphens
                return plate.replace(' ', '').replace('-', '')

        return None

    def _extract_brand(self, message: str) -> Optional[str]:
        """Extract vehicle brand from message.

        Args:
            message: Message text (lowercase)

        Returns:
            Capitalized brand name or None
        """
        # Check for each brand
        for brand in VEHICLE_BRANDS:
            # Look for brand as whole word
            pattern = r'\b' + re.escape(brand) + r'\b'
            if re.search(pattern, message):
                # Return capitalized brand
                return brand.capitalize()

        return None
