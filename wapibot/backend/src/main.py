"""FastAPI application entry point.

Modern async lifespan management for DSPy configuration.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.dspy_config import dspy_configurator
from api.router_registry import register_all_routes

# Setup logging
logging.basicConfig(
    level=settings.log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic.

    Modern FastAPI 0.115+ lifespan handler.
    """
    # Startup
    logger.info("🚀 Starting WapiBot Backend V2...")

    # Configure DSPy with selected LLM provider
    try:
        dspy_configurator.configure()
        logger.info(f"✅ DSPy configured with {settings.primary_llm_provider}")
    except Exception as e:
        logger.error(f"❌ DSPy configuration failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down WapiBot Backend V2...")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all API routers (centralized in router_registry.py)
register_all_routes(app)


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "llm_provider": settings.primary_llm_provider,
        "environment": settings.environment
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "dspy_configured": dspy_configurator.primary_lm is not None,
        "provider": settings.primary_llm_provider
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower()
    )
