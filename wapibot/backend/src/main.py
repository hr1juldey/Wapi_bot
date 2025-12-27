"""FastAPI application entry point.

Modern async lifespan management with multi-process orchestration.
Single terminal mode: auto-starts Redis, ngrok, Celery, and FastAPI.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from core.config import settings
from core.dspy_config import dspy_configurator
from core.warmup import warmup_service
from core.checkpointer import checkpointer_manager
from db.connection import db_connection
from db.websocket_db import websocket_db_connection
from core.redis_subscriber import redis_subscriber
from api.router_registry import register_all_routes

# Multi-process and middleware management
from core.redis_manager import ensure_redis_running
from utils.ngrok_manager import start_ngrok_tunnel
from utils.celery_manager import start_celery_worker
from core.shutdown_handler import shutdown_manager
from core.middleware_setup import setup_middleware

# Setup logging
logging.basicConfig(level=settings.log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


# ============================================================================
# FastAPI Lifespan: Multi-Process Orchestration
# ============================================================================


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan with multi-process management.

    Starts: Redis, ngrok, Celery, Database, DSPy, Checkpointers, Warmup.
    """
    logger.info("🚀 Starting WapiBot (Single Terminal Mode)")
    logger.info("=" * 70)

    # Step 1: Redis
    logger.info("📋 1/5: Checking Redis...")
    if not ensure_redis_running():
        raise RuntimeError("Redis required for Celery")

    # Step 2: ngrok
    logger.info("📋 2/5: Starting ngrok...")
    tunnel_url = start_ngrok_tunnel(port=settings.port)
    shutdown_manager.register_ngrok(tunnel_url)

    # Step 3: Celery
    logger.info("📋 3/5: Starting Celery...")
    worker_process = start_celery_worker()
    shutdown_manager.register_celery(worker_process)

    # Register shutdown handlers
    shutdown_manager.register_signal_handlers()

    # Step 4: Database, DSPy, Checkpointers
    logger.info("📋 4/5: Initializing Database...")
    await db_connection.init_tables()
    logger.info("✅ Database initialized")

    await websocket_db_connection.init_tables()
    logger.info("✅ WebSocket database initialized")

    dspy_configurator.configure()
    logger.info(f"✅ DSPy configured ({settings.primary_llm_provider})")

    await checkpointer_manager.initialize()
    logger.info("✅ Checkpointers initialized")

    # Step 5: Background tasks
    logger.info("📋 5/5: Starting Background Services...")
    asyncio.create_task(warmup_service.startup_warmup())
    asyncio.create_task(warmup_service.start_idle_monitor())

    # Start Redis Streams subscriber for WebSocket message delivery
    if settings.websocket_enabled:
        await redis_subscriber.start()
        logger.info("✅ Redis Streams subscriber started (WebSocket messages)")

    logger.info("=" * 70)
    logger.info("✅ All services started!")
    logger.info(f"   • FastAPI:  http://localhost:{settings.port}")
    logger.info(f"   • ngrok:    {tunnel_url or 'Not running'}")
    logger.info(f"   • Celery:   PID {worker_process.pid if worker_process else 'N/A'}")
    logger.info("   • Redis:    localhost:6379")
    logger.info("=" * 70)
    logger.info("💡 Ctrl+C to stop all services")
    logger.info("")

    yield

    # Shutdown
    logger.info("🛑 Shutting down...")

    # Stop Redis Streams subscriber
    if settings.websocket_enabled:
        await redis_subscriber.stop()
        logger.info("✅ Redis Streams subscriber stopped")

    await checkpointer_manager.shutdown()


# ============================================================================
# FastAPI App Creation and Configuration
# ============================================================================

# Create app
app = FastAPI(title=settings.app_name, version=settings.app_version, debug=settings.debug, lifespan=lifespan)

# Setup middleware (security, CORS, rate limiting, activity tracking)
setup_middleware(app)

# Register API routers
register_all_routes(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=settings.reload, log_level=settings.log_level.lower())
