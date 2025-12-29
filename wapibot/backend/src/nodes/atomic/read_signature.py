"""Utility to list and read available DSPy signatures.

Useful for:
- Visual node editor UI (show available signatures in dropdown)
- Dynamic configuration
- Introspection and debugging

Usage:
    # List all available signatures
    signatures = list_signatures()
    # Returns: ["NameExtractionSignature", "PhoneExtractionSignature", ...]

    # Get signature details
    details = get_signature_details("NameExtractionSignature")
    # Returns: {"name": "...", "fields": [...], "module_path": "..."}

    # Import signature dynamically
    signature_class = import_signature("NameExtractionSignature")
"""

import importlib
import inspect
import logging
from typing import List, Dict, Any, Optional, Type
import dspy

logger = logging.getLogger(__name__)


def list_signatures(base_path: Optional[str] = None) -> List[Dict[str, str]]:
    """List all available DSPy signatures in the project.

    Scans dspy_signatures/ directory for all Signature classes.

    Args:
        base_path: Optional base path to scan (defaults to dspy_signatures/)

    Returns:
        List of signature info dicts with name, module, and description

    Example:
        [
            {
                "name": "NameExtractionSignature",
                "module": "dspy_signatures.extraction.name_signature",
                "description": "Extract customer name from conversation",
                "fields": ["first_name", "last_name", "confidence"]
            },
            ...
        ]
    """
    if base_path is None:
        # Default to dspy_signatures directory
        from pathlib import Path
        base_path = Path(__file__).parent.parent / "dspy_signatures"

    signatures = []

    try:
        # Scan all Python files in dspy_signatures/
        for py_file in Path(base_path).rglob("*.py"):
            if py_file.name == "__init__.py":
                continue

            # Convert path to module name
            relative_path = py_file.relative_to(Path(base_path).parent)
            module_name = str(relative_path.with_suffix("")).replace("/", ".")

            try:
                # Import the module
                module = importlib.import_module(module_name)

                # Find all Signature classes
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Check if it's a dspy.Signature subclass
                    if (issubclass(obj, dspy.Signature) and
                        obj is not dspy.Signature and
                        name.endswith("Signature")):

                        # Get signature fields
                        fields = []
                        if hasattr(obj, "__annotations__"):
                            fields = list(obj.__annotations__.keys())

                        # Get docstring as description
                        description = obj.__doc__.strip() if obj.__doc__ else ""

                        signatures.append({
                            "name": name,
                            "module": module_name,
                            "description": description,
                            "fields": fields,
                            "file_path": str(py_file)
                        })

            except Exception as e:
                logger.debug(f"Error importing {module_name}: {e}")
                continue

    except Exception as e:
        logger.error(f"Error scanning signatures: {e}")

    return signatures


def get_signature_details(signature_name: str) -> Optional[Dict[str, Any]]:
    """Get detailed information about a specific signature.

    Args:
        signature_name: Name of the signature class

    Returns:
        Dict with signature details or None if not found

    Example:
        details = get_signature_details("NameExtractionSignature")
        {
            "name": "NameExtractionSignature",
            "module": "dspy_signatures.extraction.name_signature",
            "description": "Extract customer name...",
            "input_fields": ["conversation_history", "user_message", "context"],
            "output_fields": ["first_name", "last_name", "confidence"],
            "field_types": {
                "first_name": "str",
                "last_name": "str",
                "confidence": "str"
            }
        }
    """
    all_signatures = list_signatures()

    for sig_info in all_signatures:
        if sig_info["name"] == signature_name:
            return sig_info

    return None


def import_signature(signature_name: str) -> Optional[Type[dspy.Signature]]:
    """Dynamically import a signature class by name.

    Args:
        signature_name: Name of the signature class

    Returns:
        Signature class or None if not found

    Example:
        NameSig = import_signature("NameExtractionSignature")
        extractor = dspy.ChainOfThought(NameSig)
    """
    sig_info = get_signature_details(signature_name)

    if not sig_info:
        logger.error(f"Signature not found: {signature_name}")
        return None

    try:
        module = importlib.import_module(sig_info["module"])
        signature_class = getattr(module, signature_name)
        return signature_class

    except Exception as e:
        logger.error(f"Error importing {signature_name}: {e}")
        return None


def list_signatures_json() -> str:
    """List all signatures as JSON string.

    Useful for API endpoints that need to expose available signatures.

    Example:
        @app.get("/api/signatures")
        def get_signatures():
            return list_signatures_json()
    """
    import json
    signatures = list_signatures()
    return json.dumps(signatures, indent=2)
