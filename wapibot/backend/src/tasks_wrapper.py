"""Celery wrapper module for command-line worker startup.

Re-exports celery_app from tasks module for Celery CLI discovery.
Allows running: celery -A backend.src.tasks_wrapper worker --loglevel=info

Location: backend/src/
Usage: From project root, run: celery -A backend.src.tasks_wrapper worker
"""

import sys
from pathlib import Path

# Add backend/src to Python path for Celery subprocess
# This allows tasks/__init__.py to import from core, models, etc.
backend_src = Path(__file__).parent
if str(backend_src) not in sys.path:
    sys.path.insert(0, str(backend_src))

from tasks import celery_app

__all__ = ["celery_app"]
