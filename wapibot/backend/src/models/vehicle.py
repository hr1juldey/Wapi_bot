"""Vehicle-related domain models.

Provides validated models for vehicle brand and details
with support for international and Indian manufacturers.
"""

import re
from enum import Enum
from typing import Optional, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from models.core import ExtractionMetadata


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

    @model_validator(mode='after')
    def validate_vehicle_details(self):
        """Validate vehicle details consistency."""
        # Number plate validation (if present)
        if self.number_plate and self.number_plate.strip():
            plate_cleaned = self.number_plate \
                .replace(' ', '').replace('-', '') \
                .replace('.', '').upper()

            if not (1 <= len(plate_cleaned) <= 15):
                raise ValueError("Number plate length unreasonable")

        # Model name validation (if present)
        if self.model and len(self.model.strip()) < 1:
            raise ValueError("Vehicle model cannot be empty")

        # Brand validation (if present)
        if isinstance(self.brand, str) and self.brand:
            if len(self.brand.strip()) < 1:
                raise ValueError("Brand name too short")

        return self

    @field_validator('brand', 'model', 'number_plate')
    @classmethod
    def normalize_vehicle_fields(
        cls,
        v: Optional[Union[str, VehicleBrand]]
    ) -> Optional[Union[str, VehicleBrand]]:
        """Normalize vehicle fields (None allowed)."""
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
