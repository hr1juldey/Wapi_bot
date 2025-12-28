"""Pydantic model schema utilities for frontend/API use."""

import json
import logging
from typing import Optional, Dict, Any, Type, List
from pydantic import BaseModel

logger = logging.getLogger(__name__)


def list_models_json(models: List[Dict[str, Any]]) -> str:
    """Convert models list to JSON string.

    Args:
        models: List of model info dicts

    Returns:
        JSON string

    Example:
        @app.get("/api/models")
        def get_models():
            models = list_models()
            return list_models_json(models)
    """
    return json.dumps(models, indent=2)


def get_model_schema(model_class: Type[BaseModel]) -> Optional[Dict[str, Any]]:
    """Get JSON schema for a Pydantic model.

    Useful for generating forms or validation in frontend.

    Args:
        model_class: Pydantic model class

    Returns:
        JSON schema dict or None on error

    Example:
        from models.customer import Name
        schema = get_model_schema(Name)
        # Use schema to generate a form in frontend
    """
    try:
        return model_class.model_json_schema()
    except Exception as e:
        logger.error(f"Error getting schema: {e}")
        return None