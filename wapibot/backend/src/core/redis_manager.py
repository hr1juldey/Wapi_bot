"""Redis connection management and auto-start via docker-compose.

Provides health check and automatic startup for Redis.
"""

import logging
import subprocess
import time
from pathlib import Path
from typing import Optional

import redis as redis_client

logger = logging.getLogger(__name__)


def check_redis_connection(
    host: str = 'localhost',
    port: int = 6379,
    db: int = 0,
    timeout: int = 2
) -> bool:
    """Check if Redis is accessible.

    Args:
        host: Redis host (default: localhost)
        port: Redis port (default: 6379)
        db: Redis database number (default: 0)
        timeout: Connection timeout in seconds (default: 2)

    Returns:
        True if Redis responds to PING, False otherwise
    """
    try:
        r = redis_client.Redis(host=host, port=port, db=db, socket_timeout=timeout)
        r.ping()
        return True
    except (redis_client.ConnectionError, redis_client.TimeoutError):
        return False


def ensure_redis_running(
    compose_file: Optional[Path] = None,
    max_wait_seconds: int = 10
) -> bool:
    """Ensure Redis is running, auto-start via docker-compose if not.

    Args:
        compose_file: Path to docker-compose.yml (auto-detected if None)
        max_wait_seconds: Max seconds to wait for Redis after starting

    Returns:
        True if Redis is running, False if failed to start
    """
    # Check if already running
    if check_redis_connection():
        logger.info("✅ Redis already running")
        return True

    # Auto-detect compose file if not provided
    if compose_file is None:
        # Path: backend/src/core/redis_manager.py → ../../../docker-compose.yml
        project_root = Path(__file__).parent.parent.parent.parent
        compose_file = project_root / "docker-compose.yml"

    logger.info("🐳 Starting Redis via docker-compose...")

    try:
        # Start Redis via docker-compose
        subprocess.run(
            ["docker-compose", "-f", str(compose_file), "up", "-d", "redis"],
            check=True,
            capture_output=True,
            text=True
        )

        # Wait for Redis to be ready
        for _ in range(max_wait_seconds):
            time.sleep(1)
            if check_redis_connection():
                logger.info("✅ Redis started successfully")
                return True

        logger.error("❌ Redis started but not responding")
        return False

    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Failed to start Redis: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"❌ Redis startup error: {e}")
        return False
