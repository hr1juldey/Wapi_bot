"""Module versioning and checkpoint management system.

Handles:
- Version naming (v0.0 baseline, v1.0/v1.1 minor, v2.0 major)
- Metadata storage (GEPA config, metrics, timestamps)
- Rollback support (keep last 5 versions)
- A/B testing support (load specific versions)
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)


class ModuleVersioning:
    """Manage versioned checkpoints of optimized DSPy modules."""

    def __init__(self, base_dir: str = "optimized_modules"):
        """Initialize versioning system.

        Args:
            base_dir: Root directory for storing module versions
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)

        # Create subdirectories for each module type
        for module_name in ["conflict", "intent", "quality", "goals", "response"]:
            (self.base_dir / module_name).mkdir(exist_ok=True)

    def save_module(
        self,
        module_name: str,
        module: Any,
        version: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Save optimized module with version and metadata.

        Args:
            module_name: Module type (conflict, intent, quality, goals, response)
            module: DSPy module instance
            version: Version string (v1.0, v1.1, v2.0, etc.)
            metadata: Version metadata (GEPA config, metrics, etc.)

        Returns:
            Path to saved module file
        """
        module_dir = self.base_dir / module_name
        timestamp = datetime.utcnow().strftime("%Y%m%d")
        filename = f"{version}_{timestamp}.json"
        filepath = module_dir / filename

        # Save module state
        module.save(str(filepath))

        # Save metadata
        metadata_path = module_dir / f"{version}_{timestamp}_metadata.json"
        full_metadata = {
            "version": version,
            "timestamp": datetime.utcnow().isoformat(),
            "module_name": module_name,
            **metadata
        }

        with open(metadata_path, 'w') as f:
            json.dump(full_metadata, f, indent=2)

        # Update "latest" symlink
        latest_path = module_dir / "latest.json"
        if latest_path.exists() or latest_path.is_symlink():
            latest_path.unlink()
        latest_path.symlink_to(filename)

        logger.info(f"💾 Saved {module_name} {version} → {filepath}")

        # Cleanup old versions (keep last 5)
        self._cleanup_old_versions(module_dir)

        return str(filepath)

    def load_module(
        self,
        module_name: str,
        module_class: type,
        version: Optional[str] = None
    ) -> tuple[Any, Dict[str, Any]]:
        """Load module checkpoint by version.

        Args:
            module_name: Module type
            module_class: DSPy module class to instantiate
            version: Version to load (None = latest)

        Returns:
            Tuple of (loaded module, metadata)
        """
        module_dir = self.base_dir / module_name

        if version is None:
            # Load latest
            latest_path = module_dir / "latest.json"
            if not latest_path.exists():
                raise FileNotFoundError(f"No versions found for {module_name}")
            filepath = latest_path.resolve()
        else:
            # Load specific version
            matching_files = list(module_dir.glob(f"{version}_*.json"))
            if not matching_files:
                raise FileNotFoundError(f"Version {version} not found for {module_name}")
            filepath = matching_files[0]  # Get most recent if multiple

        # Load module
        module = module_class()
        module.load(str(filepath))

        # Load metadata
        metadata_path = filepath.with_name(filepath.stem + "_metadata.json")
        if metadata_path.exists():
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        else:
            metadata = {"version": "unknown"}

        logger.info(f"📦 Loaded {module_name} {metadata.get('version', 'unknown')}")

        return module, metadata

    def list_versions(self, module_name: str) -> List[Dict[str, Any]]:
        """List all available versions for a module.

        Args:
            module_name: Module type

        Returns:
            List of version metadata dicts
        """
        module_dir = self.base_dir / module_name
        metadata_files = sorted(module_dir.glob("*_metadata.json"))

        versions = []
        for meta_file in metadata_files:
            with open(meta_file, 'r') as f:
                metadata = json.load(f)
                versions.append(metadata)

        return sorted(versions, key=lambda x: x.get('timestamp', ''), reverse=True)

    def _cleanup_old_versions(self, module_dir: Path, keep_last: int = 5):
        """Remove old versions, keeping only last N.

        Args:
            module_dir: Directory containing module versions
            keep_last: Number of versions to keep
        """
        # Get all module files (exclude metadata and symlinks)
        module_files = [
            f for f in module_dir.glob("v*.json")
            if not f.is_symlink() and "_metadata" not in f.name
        ]

        # Sort by modification time (newest first)
        module_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # Remove old files
        for old_file in module_files[keep_last:]:
            old_file.unlink()
            # Also remove associated metadata
            metadata_file = old_file.with_name(old_file.stem + "_metadata.json")
            if metadata_file.exists():
                metadata_file.unlink()
            logger.info(f"🗑️  Removed old version: {old_file.name}")

    def compare_versions(
        self,
        module_name: str,
        version_a: str,
        version_b: str
    ) -> Dict[str, Any]:
        """Compare metrics between two versions.

        Args:
            module_name: Module type
            version_a: First version
            version_b: Second version

        Returns:
            Comparison dict with metric differences
        """
        module_dir = self.base_dir / module_name

        # Load metadata for both versions
        meta_a_files = list(module_dir.glob(f"{version_a}_*_metadata.json"))
        meta_b_files = list(module_dir.glob(f"{version_b}_*_metadata.json"))

        if not meta_a_files or not meta_b_files:
            raise FileNotFoundError(f"Metadata not found for comparison")

        with open(meta_a_files[0], 'r') as f:
            meta_a = json.load(f)
        with open(meta_b_files[0], 'r') as f:
            meta_b = json.load(f)

        # Compare metrics
        metrics_a = meta_a.get('metrics', {})
        metrics_b = meta_b.get('metrics', {})

        comparison = {
            "module_name": module_name,
            "version_a": version_a,
            "version_b": version_b,
            "metrics_comparison": {}
        }

        for metric_name in set(metrics_a.keys()) | set(metrics_b.keys()):
            val_a = metrics_a.get(metric_name, 0.0)
            val_b = metrics_b.get(metric_name, 0.0)
            diff = val_b - val_a
            comparison["metrics_comparison"][metric_name] = {
                f"{version_a}": val_a,
                f"{version_b}": val_b,
                "difference": diff,
                "improvement_pct": (diff / val_a * 100) if val_a > 0 else 0.0
            }

        return comparison
