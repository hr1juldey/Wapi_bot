"""Internal model scanner - extracts Pydantic model metadata."""

import importlib
import inspect
import logging
from pathlib import Path
from typing import Dict, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def scan_model_from_module(module_name: str, py_file: Path) -> list[Dict[str, Any]]:
    """Scan a Python module for Pydantic BaseModel classes.

    Args:
        module_name: Fully qualified module name
        py_file: Path to the Python file

    Returns:
        List of model info dicts
    """
    models = []

    try:
        module = importlib.import_module(module_name)

        # Find all BaseModel classes
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if not (issubclass(obj, BaseModel) and
                    obj is not BaseModel and
                    not name.startswith("_")):
                continue

            # Extract field information
            fields = {}
            if hasattr(obj, "model_fields"):
                for field_name, field_info in obj.model_fields.items():
                    fields[field_name] = {
                        "type": str(field_info.annotation),
                        "required": field_info.is_required(),
                        "description": field_info.description or "",
                        "default": str(field_info.default) if field_info.default is not None else None
                    }

            # Extract validators
            validators = [
                attr_name for attr_name in dir(obj)
                if callable(getattr(obj, attr_name)) and (
                    attr_name.startswith("validate_") or
                    hasattr(getattr(obj, attr_name), "__validator_config__")
                )
            ]

            models.append({
                "name": name,
                "module": module_name,
                "description": obj.__doc__.strip() if obj.__doc__ else "",
                "fields": fields,
                "validators": validators,
                "file_path": str(py_file)
            })

    except Exception as e:
        logger.debug(f"Error scanning {module_name}: {e}")

    return models