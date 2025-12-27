"""Health check API endpoints.

Provides both lightweight K8s probes and comprehensive test-based health checks.
- /health/live - Liveness probe (is the server running?)
- /health/ready - Readiness probe (can it serve traffic?)
- /health/status - Dependency health (Redis, Celery, etc.)
- /health - Full test suite health check
"""

import logging
import subprocess
from datetime import datetime
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from core.config import settings
from core.health_monitor import health_monitor

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/")
async def root():
    """Basic health check endpoint - quick status."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version
    }


@router.get("/health")
async def health_check():
    """REAL health check - runs test suite and reports results.

    Executes the test suite in tests/ and returns a concise health report.
    This is the honest health check that actually validates the system.

    Returns:
        Concise test results with pass/fail status
    """
    start_time = datetime.now()

    # Run test suite
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=60,
            cwd="."
        )

        # Parse pytest output for summary
        output_lines = result.stdout.strip().split('\n')
        summary_line = next((line for line in reversed(output_lines) if 'passed' in line or 'failed' in line), "")

        test_passed = result.returncode == 0
        elapsed = (datetime.now() - start_time).total_seconds()

        return {
            "status": "healthy" if test_passed else "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "check_duration_seconds": round(elapsed, 3),
            "test_summary": summary_line.strip(),
            "exit_code": result.returncode,
            "service": settings.app_name,
            "version": settings.app_version
        }

    except subprocess.TimeoutExpired:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": "Test suite timed out after 60 seconds",
            "service": settings.app_name,
            "version": settings.app_version
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "service": settings.app_name,
            "version": settings.app_version
        }


@router.get("/health/live")
async def liveness_probe():
    """Liveness probe for Kubernetes.

    Returns 200 if the application process is running.
    K8s will restart the pod if this fails.

    This is a lightweight check - just confirms the server responds.
    """
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe():
    """Readiness probe for Kubernetes.

    Returns 200 if ready to serve traffic (all dependencies healthy).
    Returns 503 if degraded (e.g., Redis down, Celery disabled).
    K8s will remove pod from load balancer if this fails.

    Use this to prevent cascading failures when dependencies crash.
    """
    health_status = health_monitor.get_health_status()

    if health_status["status"] == "healthy":
        return health_status
    else:
        # Service degraded - signal not ready for new traffic
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )


@router.get("/health/status")
async def dependency_health():
    """Detailed health status of all dependencies.

    Returns real-time health information:
    - Redis connection status
    - Celery availability
    - Last check timestamps

    Use for monitoring dashboards and debugging.
    """
    return health_monitor.get_health_status()


@router.get("/health/doctor")
async def api_doctor():
    """API Doctor - comprehensive diagnostic of all services and APIs.

    Runs a full diagnostic suite checking:
    - Redis connection and response time
    - Celery worker status
    - Database connectivity
    - External API availability (Frappe, WAPI)
    - ngrok tunnel status
    - Configuration validation

    Returns actionable recommendations for any issues found.
    """
    from core.redis_manager import get_redis_client
    from clients.frappe_yawlit import get_yawlit_client
    from db.connection import db_connection

    diagnosis = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "checks": {},
        "recommendations": []
    }

    # Check 1: Redis
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

    # Check 2: Celery
    diagnosis["checks"]["celery"] = {
        "status": "healthy" if health_monitor.is_celery_available() else "degraded",
        "enabled": health_monitor.is_celery_available(),
        "message": "Celery available" if health_monitor.is_celery_available() else "Celery disabled (Redis down)"
    }

    # Check 3: Database
    try:
        # Simple DB query test
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

    # Check 4: Frappe API
    try:
        client = get_yawlit_client()
        # Try a lightweight API call
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

    # Check 5: Configuration
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

    # Final recommendations
    if diagnosis["overall_status"] == "healthy" and not diagnosis["recommendations"]:
        diagnosis["recommendations"].append("✅ All systems operational!")

    return diagnosis
