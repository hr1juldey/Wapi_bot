"""Health check diagnostic functions.

Split from health_api.py to maintain 100-line limit.
"""

from datetime import datetime
from typing import Dict, Any

from core.config import settings
from core.health_monitor import health_monitor


async def check_redis_health(diagnosis: Dict[str, Any]) -> None:
    """Check Redis connection and latency."""
    from core.redis_manager import get_redis_client

    try:
        redis_client = get_redis_client()
        start = datetime.now()
        await redis_client.ping()
        latency_ms = (datetime.now() - start).total_seconds() * 1000

        diagnosis["checks"]["redis"] = {
            "status": "healthy",
            "latency_ms": round(latency_ms, 2),
            "message": "Redis responding normally"
        }
    except Exception as e:
        diagnosis["checks"]["redis"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "Redis connection failed"
        }
        diagnosis["overall_status"] = "unhealthy"
        diagnosis["recommendations"].append("Start Redis: sudo systemctl start redis")


async def check_celery_health(diagnosis: Dict[str, Any]) -> None:
    """Check Celery worker status."""
    diagnosis["checks"]["celery"] = {
        "status": "healthy" if health_monitor.is_celery_available() else "degraded",
        "enabled": health_monitor.is_celery_available(),
        "message": "Celery available" if health_monitor.is_celery_available()
                   else "Celery disabled (Redis down)"
    }


async def check_database_health(diagnosis: Dict[str, Any]) -> None:
    """Check database connectivity."""
    try:
        diagnosis["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection OK"
        }
    except Exception as e:
        diagnosis["checks"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
            "message": "Database connection failed"
        }
        diagnosis["overall_status"] = "unhealthy"
        diagnosis["recommendations"].append("Check database migrations: alembic upgrade head")


async def check_frappe_api_health(diagnosis: Dict[str, Any]) -> None:
    """Check Frappe API client initialization."""
    from clients.frappe_yawlit import get_yawlit_client

    try:
        get_yawlit_client()
        diagnosis["checks"]["frappe_api"] = {
            "status": "unknown",
            "message": "Frappe client initialized (add live test if needed)"
        }
    except Exception as e:
        diagnosis["checks"]["frappe_api"] = {
            "status": "degraded",
            "error": str(e),
            "message": "Frappe client initialization issue"
        }
        diagnosis["recommendations"].append("Check FRAPPE_BASE_URL and API credentials in .env")


async def check_configuration_health(diagnosis: Dict[str, Any]) -> None:
    """Validate required environment configuration."""
    config_issues = []

    if not settings.frappe_api_key:
        config_issues.append("FRAPPE_API_KEY not set")
    if not settings.frappe_api_secret:
        config_issues.append("FRAPPE_API_SECRET not set")
    if not settings.wapi_access_token:
        config_issues.append("WAPI_ACCESS_TOKEN not set")

    if config_issues:
        diagnosis["checks"]["configuration"] = {
            "status": "degraded",
            "issues": config_issues,
            "message": f"{len(config_issues)} configuration issue(s)"
        }
        diagnosis["recommendations"].append("Review .env.txt file and add missing credentials")
    else:
        diagnosis["checks"]["configuration"] = {
            "status": "healthy",
            "message": "All required environment variables set"
        }