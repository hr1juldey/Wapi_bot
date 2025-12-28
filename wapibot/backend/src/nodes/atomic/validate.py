"""Atomic validation node - works with ANY Pydantic model.

This single node replaces validate_name.py, validate_phone.py, validate_vehicle.py, etc.
Configuration over specialization - just plugin the Pydantic model!

Usage:
    # Validate name
    validate.node(state, Name, "customer", ["first_name", "last_name"])

    # Validate phone (SAME node, different model!)
    validate.node(state, Phone, "customer", ["phone_number"])

    # Validate vehicle
    validate.node(state, Vehicle, "vehicle", ["brand", "model"])
"""

import logging
from typing import Type, Optional, Literal
from pydantic import BaseModel, ValidationError
from workflows.shared.state import BookingState
from core.brain_config import get_brain_settings
from utils.field_utils import get_nested_field, set_nested_field

logger = logging.getLogger(__name__)


async def node(
    state: BookingState,
    model: Type[BaseModel],
    data_path: str,
    fields_to_validate: Optional[list[str]] = None,
    on_failure: Optional[Literal["log", "clear", "raise"]] = None
) -> BookingState:
    """Atomic validation node - works with ANY Pydantic model.

    Args:
        state: Current booking state
        model: ANY Pydantic model class to validate against
        data_path: Path to data in state (e.g., "customer", "vehicle")
        fields_to_validate: Optional list of specific fields to validate
                           If None, validates all fields in the data
        on_failure: Action on validation failure (default: from brain settings)
                   - "log": Log error but continue
                   - "clear": Clear invalid data
                   - "raise": Raise exception
    """
    # Brain-aware defaults
    brain_settings = get_brain_settings()
    if on_failure is None:
        on_failure = "log" if brain_settings.brain_mode == "reflex" else "clear"

    # Get data from state
    data = get_nested_field(state, data_path)

    if data is None:
        logger.warning(f"⚠️ No data found at {data_path} for validation")
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"validation_no_data_{data_path}")
        return state

    # If specific fields requested, extract only those
    if fields_to_validate:
        data_to_validate = {
            field: data.get(field) for field in fields_to_validate
            if field in data
        }
    else:
        data_to_validate = data

    # Attempt validation
    try:
        logger.info(f"🔍 Validating {data_path} with {model.__name__}")

        # Create Pydantic model instance - this triggers all validations
        validated = model(**data_to_validate)

        # Validation passed - update state with validated data
        validated_dict = validated.model_dump()

        # Merge validated data back into state
        current_data = get_nested_field(state, data_path) or {}
        current_data.update(validated_dict)
        set_nested_field(state, data_path, current_data)

        logger.info(f"✅ Validation passed for {data_path}")

        # Store validation metadata
        metadata_path = f"{data_path}.validation_status"
        set_nested_field(state, metadata_path, "passed")

        return state

    except ValidationError as e:
        logger.error(f"❌ Validation failed for {data_path}: {e}")

        # Store validation errors in state
        if "errors" not in state:
            state["errors"] = []

        for error in e.errors():
            field_path = ".".join(str(loc) for loc in error["loc"])
            error_msg = f"validation_failed_{data_path}.{field_path}_{error['type']}"
            state["errors"].append(error_msg)

        # Handle failure based on strategy
        if on_failure == "clear":
            logger.warning(f"🧹 Clearing invalid data at {data_path}")
            set_nested_field(state, data_path, None)

        elif on_failure == "raise":
            raise

        # Default: "log" - just log and continue
        metadata_path = f"{data_path}.validation_status"
        set_nested_field(state, metadata_path, "failed")

        return state

    except Exception as e:
        logger.error(f"❌ Unexpected validation error for {data_path}: {e}")

        if "errors" not in state:
            state["errors"] = []
        state["errors"].append(f"validation_error_{data_path}")

        if on_failure == "raise":
            raise

        return state
