"""Health check API endpoints.

Provides both lightweight K8s probes and comprehensive test-based health checks.
- /health/live - Liveness probe (is the server running?)
- /health/ready - Readiness probe (can it serve traffic?)
- /health/status - Dependency health (Redis, Celery, etc.)
- /health/doctor - Full diagnostic with actionable recommendations
- /health - Full test suite health check
"""

import logging
import subprocess
from datetime import datetime
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from core.config import settings
from core.health_monitor import health_monitor
from api.health_checks import (
    check_redis_health,
    check_celery_health,
    check_database_health,
    check_frappe_api_health,
    check_configuration_health
)

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
        summary_line = next((line for line in reversed(output_lines)
                           if 'passed' in line or 'failed' in line), "")

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
    """Liveness probe for Kubernetes - is the server process alive?"""
    return {"status": "alive"}


@router.get("/health/ready")
async def readiness_probe():
    """Readiness probe for Kubernetes - can the server serve traffic?

    Returns 503 if degraded (dependencies down).
    K8s removes pod from load balancer rotation on 503.
    """
    health_status = health_monitor.get_health_status()

    if health_status["status"] == "healthy":
        return health_status
    else:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=health_status
        )


@router.get("/health/status")
async def dependency_health():
    """Real-time health status of all dependencies.

    Returns: Redis, Celery, last check timestamps
    """
    return health_monitor.get_health_status()


@router.get("/health/doctor")
async def api_doctor():
    """API Doctor - comprehensive diagnostic with actionable fixes.

    Checks: Redis, Celery, Database, Frappe API, Configuration
    Returns: Status + recommendations for each issue
    """
    diagnosis = {
        "timestamp": datetime.now().isoformat(),
        "overall_status": "healthy",
        "checks": {},
        "recommendations": []
    }

    # Run all diagnostic checks
    await check_redis_health(diagnosis)
    await check_celery_health(diagnosis)
    await check_database_health(diagnosis)
    await check_frappe_api_health(diagnosis)
    await check_configuration_health(diagnosis)

    # Final recommendations
    if diagnosis["overall_status"] == "healthy" and not diagnosis["recommendations"]:
        diagnosis["recommendations"].append("✅ All systems operational!")

    return diagnosis
