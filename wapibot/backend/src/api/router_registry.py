"""Central router registry for all API endpoints.

Add all new routers here to keep main.py clean.
"""

from fastapi import FastAPI

from api.health_api import router as health_router
from api.v1.chat_endpoint import router as chat_router
from api.v1.wapi_webhook import router as wapi_router
from api.v1.admin_payment_endpoint import router as payment_router
from api.v1.qr_endpoint import router as qr_router
from api.v1.brain_endpoint import router as brain_router
from api.v1.ws_chat_endpoint import websocket_chat

from core.config import settings


def register_all_routes(app: FastAPI) -> None:
    """Register all API routers with the FastAPI app.

    Add new routers here as you create them.
    Keeps main.py clean and organized.

    Args:
        app: FastAPI application instance
    """
    # System routes
    app.include_router(health_router)

    # V1 API routes
    app.include_router(chat_router)
    app.include_router(wapi_router)
    app.include_router(payment_router)
    app.include_router(qr_router)
    app.include_router(brain_router)

    # WebSocket routes (must use add_websocket_route, not include_router)
    if settings.websocket_enabled:
        app.add_websocket_route("/ws/chat/{conversation_id}", websocket_chat)

    # Add more routers here as you build them:
    # app.include_router(booking_router)
    # app.include_router(analytics_router)
    # app.include_router(admin_router)
