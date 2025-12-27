"""Load optimized or baseline DSPy modules with versioning support."""

import os
import logging
from typing import Dict, Optional
import dspy
from dspy_modules.brain import (
    ConflictDetector,
    IntentPredictor,
    QualityEvaluator,
    GoalDecomposer,
    ResponseGenerator
)

logger = logging.getLogger(__name__)

MODULE_CLASSES = {
    "conflict": ConflictDetector,
    "intent": IntentPredictor,
    "quality": QualityEvaluator,
    "goals": GoalDecomposer,
    "response": ResponseGenerator
}


def load_module(
    module_name: str,
    use_optimized: bool = True,
    version: Optional[str] = None
) -> dspy.Module:
    """Load DSPy module (optimized or baseline).

    Args:
        module_name: Module type (conflict, intent, quality, goals, response)
        use_optimized: If True, try to load optimized version
        version: Specific version to load (None = latest)

    Returns:
        Loaded DSPy module instance
    """
    module_class = MODULE_CLASSES.get(module_name)
    if not module_class:
        raise ValueError(f"Unknown module: {module_name}")

    # Try loading optimized version
    if use_optimized:
        optimized_dir = f"optimized_modules/{module_name}"

        if version:
            # Load specific version
            version_files = [
                f for f in os.listdir(optimized_dir)
                if f.startswith(f"{version}_") and f.endswith(".json")
            ] if os.path.exists(optimized_dir) else []

            if version_files:
                optimized_path = os.path.join(optimized_dir, version_files[0])
            else:
                optimized_path = None
        else:
            # Load latest version
            latest_link = os.path.join(optimized_dir, "latest.json")
            optimized_path = latest_link if os.path.exists(latest_link) else None

        if optimized_path and os.path.exists(optimized_path):
            try:
                module = module_class()
                module.load(optimized_path)
                logger.info(f"✅ Loaded optimized {module_name} from {optimized_path}")
                return module
            except Exception as e:
                logger.warning(f"⚠️  Failed to load optimized {module_name}: {e}")

    # Fallback to baseline
    logger.info(f"📦 Using baseline {module_name}")
    return module_class()


def load_all_modules(
    use_optimized: bool = True,
    version: Optional[str] = None
) -> Dict[str, dspy.Module]:
    """Load all 5 brain modules.

    Args:
        use_optimized: If True, try to load optimized versions
        version: Specific version to load for all modules

    Returns:
        Dict mapping module name to loaded module instance
    """
    modules = {}

    for name in MODULE_CLASSES.keys():
        modules[name] = load_module(name, use_optimized, version)

    logger.info(f"🧠 Loaded {len(modules)} brain modules (optimized={use_optimized})")

    return modules


def save_optimized_modules(
    modules: Dict[str, dspy.Module],
    version: str = "v1.0",
    metadata: Optional[Dict] = None
) -> Dict[str, str]:
    """Save optimized modules with versioning.

    Args:
        modules: Dict of module name to module instance
        version: Version string (v1.0, v1.1, etc.)
        metadata: Optional metadata to save with each module

    Returns:
        Dict mapping module name to save path
    """
    from datetime import datetime
    from services.module_versioning import ModuleVersioning

    versioning = ModuleVersioning()
    saved_paths = {}

    for module_name, module in modules.items():
        module_metadata = metadata or {}
        module_metadata.update({
            "module_name": module_name,
            "timestamp": datetime.utcnow().isoformat()
        })

        try:
            path = versioning.save_module(
                module_name=module_name,
                module=module,
                version=version,
                metadata=module_metadata
            )
            saved_paths[module_name] = path
            logger.info(f"💾 Saved {module_name} {version}")

        except Exception as e:
            logger.error(f"❌ Failed to save {module_name}: {e}")

    return saved_paths
