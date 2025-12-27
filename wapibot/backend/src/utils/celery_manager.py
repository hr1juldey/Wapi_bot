"""Celery worker process management.

Manages Celery worker as subprocess with log streaming.
"""

import logging
import subprocess
import threading
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def start_celery_worker(
    working_directory: Optional[Path] = None,
    log_prefix: str = "[Celery]"
) -> Optional[subprocess.Popen]:
    """Start Celery worker as subprocess with log streaming.

    Args:
        working_directory: Directory to run celery from (project root)
                          Auto-detected if None
        log_prefix: Prefix for log lines (default: "[Celery]")

    Returns:
        Celery worker process (Popen object)
        None if failed to start
    """
    try:
        # Auto-detect working directory if not provided
        if working_directory is None:
            # Path: backend/src/utils/celery_manager.py → ../../../
            working_directory = Path(__file__).parent.parent.parent.parent

        # Start Celery worker (tasks_wrapper.py will be in backend/src/)
        process = subprocess.Popen(
            ["celery", "-A", "backend.src.tasks_wrapper", "worker", "--loglevel=info"],
            cwd=str(working_directory),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1  # Line buffered
        )

        logger.info(f"🔄 Celery worker started (PID: {process.pid})")

        # Stream Celery logs in background thread
        def stream_logs():
            """Stream subprocess stdout to console."""
            for line in process.stdout:
                print(f"{log_prefix} {line.rstrip()}")

        log_thread = threading.Thread(target=stream_logs, daemon=True)
        log_thread.start()

        return process

    except Exception as e:
        logger.error(f"❌ Failed to start Celery worker: {e}")
        return None


def stop_celery_worker(
    process: Optional[subprocess.Popen],
    timeout: int = 5
) -> bool:
    """Stop Celery worker gracefully.

    Args:
        process: Celery worker process
        timeout: Seconds to wait before force kill (default: 5)

    Returns:
        True if stopped successfully, False otherwise
    """
    if not process:
        return True

    try:
        logger.info("Stopping Celery worker...")
        process.terminate()

        try:
            process.wait(timeout=timeout)
            logger.info("✅ Celery worker stopped")
            return True
        except subprocess.TimeoutExpired:
            logger.warning("⚠️  Celery did not stop, forcing kill...")
            process.kill()
            return False

    except Exception as e:
        logger.error(f"❌ Error stopping Celery: {e}")
        return False
