"""Health monitoring for critical dependencies.

Prevents cascading failures by detecting and gracefully degrading when services crash.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ServiceStatus(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthMonitor:
    """Monitors health of critical dependencies and enables graceful degradation."""

    def __init__(self):
        """Initialize health monitor."""
        self.redis_healthy = True
        self.celery_enabled = True
        self.last_redis_check: Optional[datetime] = None
        self.check_interval = 30  # seconds
        self._monitoring_task: Optional[asyncio.Task] = None

    async def start_monitoring(self):
        """Start background health monitoring."""
        logger.info("🏥 Starting health monitoring...")
        self._monitoring_task = asyncio.create_task(self._monitor_loop())

    async def stop_monitoring(self):
        """Stop background health monitoring."""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("🏥 Health monitoring stopped")

    async def _monitor_loop(self):
        """Continuous health monitoring loop."""
        while True:
            try:
                await asyncio.sleep(self.check_interval)
                await self.check_redis_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Health monitor error: {e}")

    async def check_redis_health(self) -> bool:
        """Check if Redis is accessible.

        Returns:
            True if Redis is healthy, False otherwise
        """
        try:
            from core.redis_manager import get_redis_client
            redis_client = get_redis_client()

            # Try to ping Redis
            await redis_client.ping()

            # Redis is healthy
            if not self.redis_healthy:
                logger.info("✅ Redis recovered - re-enabling Celery features")
                self.redis_healthy = True
                self.celery_enabled = True

            self.last_redis_check = datetime.now()
            return True

        except Exception as e:
            # Redis is down
            if self.redis_healthy:
                logger.error(f"❌ Redis connection lost: {e}")
                logger.warning("⚠️  Entering degraded mode - disabling Celery-dependent features")
                self.redis_healthy = False
                self.celery_enabled = False
            else:
                logger.warning(f"⚠️  Redis still down: {e}")

            self.last_redis_check = datetime.now()
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status of all services.

        Returns:
            Health status dictionary for all monitored services
        """
        return {
            "status": "healthy" if self.redis_healthy else "degraded",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "redis": {
                    "status": ServiceStatus.HEALTHY.value if self.redis_healthy else ServiceStatus.UNHEALTHY.value,
                    "last_check": self.last_redis_check.isoformat() if self.last_redis_check else None,
                },
                "celery": {
                    "status": ServiceStatus.HEALTHY.value if self.celery_enabled else ServiceStatus.DEGRADED.value,
                    "enabled": self.celery_enabled,
                },
            },
        }

    def is_celery_available(self) -> bool:
        """Check if Celery features are available.

        Returns:
            True if Celery can be used, False if degraded
        """
        return self.celery_enabled


# Global health monitor instance
health_monitor = HealthMonitor()