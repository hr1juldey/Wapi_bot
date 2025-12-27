"""WapiBot entry point.

Single terminal startup: Runs backend server with Redis, ngrok, Celery, and FastAPI.

Usage:
    python main.py
    # or
    uv run main.py
"""

import sys
from pathlib import Path

# Add backend/src to Python path
project_root = Path(__file__).parent
backend_src = project_root / "backend" / "src"
sys.path.insert(0, str(backend_src))


def main():
    """Start WapiBot backend with all services."""
    import uvicorn
    from core.config import settings

    # Run FastAPI server (lifespan handles Redis, ngrok, Celery startup)
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )


if __name__ == "__main__":
    main()
