"""Graceful shutdown handler for multi-process application.

Handles Ctrl+C and SIGTERM signals to cleanly stop all services.
"""

import logging
import signal
import sys
import subprocess
from typing import Optional, Callable

from utils.celery_manager import stop_celery_worker
from utils.ngrok_manager import stop_ngrok_tunnel

logger = logging.getLogger(__name__)


class ShutdownManager:
    """Manages graceful shutdown of multiple services."""

    def __init__(self, reload_mode: bool = False):
        """Initialize shutdown manager.

        Args:
            reload_mode: If True, don't call sys.exit() to allow uvicorn hot reload
        """
        self.celery_process: Optional[subprocess.Popen] = None
        self.ngrok_tunnel_url: Optional[str] = None
        self.cleanup_callbacks: list[Callable] = []
        self.should_exit: bool = not reload_mode  # Don't exit in reload mode

    def register_celery(self, process: Optional[subprocess.Popen]):
        """Register Celery worker process for shutdown.

        Args:
            process: Celery worker subprocess
        """
        self.celery_process = process

    def register_ngrok(self, tunnel_url: Optional[str]):
        """Register ngrok tunnel for shutdown.

        Args:
            tunnel_url: ngrok public URL
        """
        self.ngrok_tunnel_url = tunnel_url

    def add_cleanup_callback(self, callback: Callable):
        """Add custom cleanup callback.

        Args:
            callback: Function to call during shutdown
        """
        self.cleanup_callbacks.append(callback)

    def shutdown(self, signum=None, frame=None):
        """Handle shutdown signal (Ctrl+C or SIGTERM).

        Args:
            signum: Signal number
            frame: Current stack frame
        """
        logger.info("🛑 Shutdown signal received (Ctrl+C)...")

        # Stop Celery worker
        if self.celery_process:
            logger.info("   Stopping Celery worker...")
            stop_celery_worker(self.celery_process)

        # Stop ngrok tunnel
        if self.ngrok_tunnel_url:
            logger.info("   Stopping ngrok tunnel...")
            stop_ngrok_tunnel(self.ngrok_tunnel_url)

        # Run custom cleanup callbacks
        for callback in self.cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                logger.warning(f"   ⚠️  Cleanup callback failed: {e}")

        logger.info("👋 All services stopped. Goodbye!")

        # Exit strategy depends on reload mode
        if self.should_exit:
            # Production mode: clean exit
            logger.info("   Exiting process...")
            sys.exit(0)
        else:
            # Reload mode: restore default handler and re-raise signal
            # This allows uvicorn to handle the signal for hot reload
            logger.info("   Re-raising signal for uvicorn to handle...")
            signal.signal(signum or signal.SIGINT, signal.SIG_DFL)
            if signum:
                signal.raise_signal(signum)

    def register_signal_handlers(self):
        """Register SIGINT and SIGTERM handlers."""
        signal.signal(signal.SIGINT, self.shutdown)
        signal.signal(signal.SIGTERM, self.shutdown)


# Global shutdown manager instance (configured by main.py)
# Default to reload_mode=False for safety
shutdown_manager = ShutdownManager(reload_mode=False)
