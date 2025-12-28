"""Utility to list and read available Pydantic models.

Useful for:
- Visual node editor UI (show available models in dropdown for validation)
- Dynamic validation configuration
- Introspection and debugging

Usage:
    # List all available Pydantic models
    models = list_models()

    # Get model details
    details = get_model_details("Name")

    # Import model dynamically
    model_class = import_model("Name")
"""

import importlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel

from ._model_scanner import scan_model_from_module

logger = logging.getLogger(__name__)


def list_models(base_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all available Pydantic models in the project.

    Args:
        base_path: Optional base path to scan (defaults to models/)

    Returns:
        List of model info dicts with name, module, fields, and validators
    """
    if base_path is None:
        base_path = Path(__file__).parent.parent / "models"

    models = []

    try:
        # Scan all Python files in models/
        for py_file in Path(base_path).rglob("*.py"):
            if py_file.name in ("__init__.py", "core.py"):
                continue

            # Convert path to module name
            relative_path = py_file.relative_to(Path(base_path).parent)
            module_name = str(relative_path.with_suffix("")).replace("/", ".")

            # Scan module for models
            models.extend(scan_model_from_module(module_name, py_file))

    except Exception as e:
        logger.error(f"Error scanning models: {e}")

    return models


def get_model_details(model_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific Pydantic model.

    Args:
        model_name: Name of the model class

    Returns:
        Dict with model details or None if not found
    """
    for model_info in list_models():
        if model_info["name"] == model_name:
            return model_info
    return None


def import_model(model_name: str) -> Optional[Type[BaseModel]]:
    """Dynamically import a Pydantic model class by name.

    Args:
        model_name: Name of the model class

    Returns:
        Model class or None if not found

    Example:
        Name = import_model("Name")
        validated = Name(first_name="Hrijul", last_name="Dey")
    """
    model_info = get_model_details(model_name)

    if not model_info:
        logger.error(f"Model not found: {model_name}")
        return None

    try:
        module = importlib.import_module(model_info["module"])
        return getattr(module, model_name)
    except Exception as e:
        logger.error(f"Error importing {model_name}: {e}")
        return None