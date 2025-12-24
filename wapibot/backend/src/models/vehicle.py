"""Vehicle-related domain models.

Provides validated models for vehicle brand and details
with support for international and Indian manufacturers.
"""

import re
from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from models.core import ExtractionMetadata


# Valid Indian state RTO codes
INDIAN_STATE_CODES = {
    'AN', 'AP', 'AR', 'AS', 'BR', 'CG', 'CH', 'DD', 'DL', 'DN',
    'GA', 'GJ', 'HP', 'HR', 'JH', 'JK', 'KA', 'KL', 'LA', 'LD',
    'MH', 'ML', 'MN', 'MP', 'MZ', 'NL', 'OD', 'OR', 'PB', 'PY',
    'RJ', 'SK', 'TN', 'TR', 'TS', 'UK', 'UP', 'WB'
}

# Known vehicle brands for regex matching (lowercase)
VEHICLE_BRANDS = [
    "tata", "mahindra", "maruti", "suzuki", "honda", "toyota", "hyundai",
    "ford", "chevrolet", "nissan", "volkswagen", "bmw", "mercedes", "audi",
    "kia", "mg", "renault", "skoda", "jeep", "fiat", "volvo", "jaguar"
]


class VehicleBrand(str, Enum):
    """Vehicle brands including Indian manufacturers."""

    # International Brands
    TOYOTA = "Toyota"
    HONDA = "Honda"
    FORD = "Ford"
    CHEVROLET = "Chevrolet"
    BMW = "BMW"
    MERCEDES = "Mercedes-Benz"
    AUDI = "Audi"
    TESLA = "Tesla"
    NISSAN = "Nissan"
    HYUNDAI = "Hyundai"
    KIA = "Kia"
    SUBARU = "Subaru"
    MAZDA = "Mazda"
    LEXUS = "Lexus"
    VOLKSWAGEN = "Volkswagen"
    SKODA = "Skoda"
    MG_MOTOR = "MG Motor"
    PEUGEOT = "Peugeot"
    CITROEN = "Citroen"

    # Indian Brands
    TATA = "Tata"
    MAHINDRA = "Mahindra"
    MARUTI = "Maruti Suzuki"
    FORCE_MOTORS = "Force Motors"
    EICHER = "Eicher Motors"
    ASHOK_LEYLAND = "Ashok Leyland"

    # Luxury Brands
    JAGUAR_LAND_ROVER = "Jaguar Land Rover"
    ASTON_MARTIN = "Aston Martin"
    LAMBORGHINI = "Lamborghini"
    FERRARI = "Ferrari"
    BENTLEY = "Bentley"


class VehicleDetails(BaseModel):
    """Validated vehicle information."""

    model_config = ConfigDict(extra='forbid')

    brand: Union[VehicleBrand, str, None] = Field(
        default=None,
        description="Vehicle brand (enum or custom string)"
    )
    model: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Vehicle model name"
    )
    number_plate: Optional[str] = Field(
        default=None,
        max_length=20,
        description="License plate (standardized format)"
    )
    metadata: ExtractionMetadata = Field(
        description="Extraction metadata"
    )

    @field_validator('number_plate')
    @classmethod
    def validate_indian_license_plate(cls, v: Optional[str]) -> Optional[str]:
        """Validate and normalize Indian license plate format.

        Supports:
        - Standard format: WB 06 AF 1234 -> WB06AF1234
        - BH series format: 22 BH 1234 AB -> 22BH1234AB

        Args:
            v: Raw license plate string

        Returns:
            Normalized plate (uppercase, no spaces/hyphens) or None

        Raises:
            ValueError: If plate format is invalid
        """
        if v is None:
            return None

        # Reject placeholder values
        if v.strip().lower() in ['none', 'unknown', 'n/a', 'tbd', '']:
            return None

        # Normalize: remove spaces, hyphens, dots, convert to uppercase
        plate = v.replace(' ', '').replace('-', '').replace('.', '').upper()

        # BH series format: 00BH0000XX (e.g., 22BH1234AB)
        # Pattern: 2 digits + BH + 4 digits + 2 letters
        bh_pattern = r'^\d{2}BH\d{4}[A-Z]{2}$'
        if re.match(bh_pattern, plate):
            return plate

        # Indian standard format: XX00XX0000 (e.g., WB06AF1234)
        # Pattern: 2 letters (state code) + 2 digits + 1-2 letters + 4 digits
        standard_pattern = r'^([A-Z]{2})(\d{2})([A-Z]{1,2})(\d{4})$'
        match = re.match(standard_pattern, plate)
        if match:
            state_code = match.group(1)
            # Validate state code against known Indian RTO codes
            if state_code in INDIAN_STATE_CODES:
                return plate
            else:
                raise ValueError(
                    f"Invalid Indian state code '{state_code}' in license plate '{v}'. "
                    f"Must be a valid RTO code (WB, DL, MH, etc.)"
                )

        # Invalid format
        raise ValueError(
            f"Invalid Indian license plate format: '{v}'. "
            f"Expected formats: 'WB06AF1234' (standard) or '22BH1234AB' (BH series)"
        )

    @model_validator(mode='after')
    def validate_vehicle_details(self):
        """Validate vehicle details consistency."""
        # Model name validation (if present)
        if self.model and len(self.model.strip()) < 1:
            raise ValueError("Vehicle model cannot be empty")

        # Brand validation (if present)
        if isinstance(self.brand, str) and self.brand:
            if len(self.brand.strip()) < 1:
                raise ValueError("Brand name too short")

        return self

    @field_validator('brand', 'model')
    @classmethod
    def normalize_vehicle_fields(
        cls,
        v: Optional[Union[str, VehicleBrand]]
    ) -> Optional[Union[str, VehicleBrand]]:
        """Normalize brand and model fields (None allowed)."""
        if v is None:
            return None

        # Enum values pass through
        if isinstance(v, VehicleBrand):
            return v

        # Empty strings become None
        if not v.strip():
            return None

        # Reject placeholder values
        if v.strip().lower() in ['none', 'unknown', 'n/a', '']:
            return None

        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', v.strip())
        return normalized
