"""Regex-based vehicle brand extraction fallback.

Fast vehicle brand detection using known brand list.
"""

import re
from typing import Optional, Dict


# Known vehicle brands (lowercase for matching)
VEHICLE_BRANDS = [
    "tata", "mahindra", "maruti", "suzuki", "honda", "toyota", "hyundai",
    "ford", "chevrolet", "nissan", "volkswagen", "bmw", "mercedes", "audi",
    "kia", "mg", "renault", "skoda", "jeep", "fiat", "volvo", "jaguar"
]


class RegexVehicleExtractor:
    """Fast vehicle brand extraction using regex."""

    def extract(self, message: str) -> Optional[Dict[str, str]]:
        """Extract vehicle brand from message.

        Args:
            message: User message text

        Returns:
            {"brand": "Honda"} or None
        """
        if not message:
            return None

        message_lower = message.lower()

        # Check for each brand
        for brand in VEHICLE_BRANDS:
            # Look for brand as whole word
            pattern = r'\b' + re.escape(brand) + r'\b'
            if re.search(pattern, message_lower):
                # Return capitalized brand
                return {
                    "brand": brand.capitalize()
                }

        return None
