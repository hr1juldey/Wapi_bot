"""ngrok tunnel management for exposing local server to internet.

Provides programmatic ngrok tunnel creation using pyngrok.
"""

import logging
from typing import Optional

from pyngrok import ngrok, conf

logger = logging.getLogger(__name__)


def start_ngrok_tunnel(
    port: int = 8000,
    region: str = "in",
    bind_tls: bool = True
) -> Optional[str]:
    """Start ngrok tunnel on specified port.

    Args:
        port: Local port to tunnel (default: 8000)
        region: ngrok region (default: "in" for India)
        bind_tls: Use HTTPS tunnel (default: True)

    Returns:
        Public ngrok URL (e.g., https://abc123.ngrok-free.app)
        None if tunnel creation failed
    """
    try:
        # Configure ngrok region (lower latency)
        conf.get_default().region = region

        # Start tunnel
        tunnel = ngrok.connect(port, bind_tls=bind_tls)
        public_url = tunnel.public_url

        logger.info(f"🌐 ngrok tunnel: {public_url} → localhost:{port}")
        return public_url

    except Exception as e:
        logger.error(f"❌ ngrok failed: {e}")
        logger.warning("⚠️  Continuing without ngrok. WAPI webhooks will not work.")
        return None


def stop_ngrok_tunnel(tunnel_url: Optional[str]) -> bool:
    """Stop ngrok tunnel.

    Args:
        tunnel_url: Public ngrok URL to disconnect

    Returns:
        True if disconnected successfully, False otherwise
    """
    if not tunnel_url:
        return True

    try:
        ngrok.disconnect(tunnel_url)
        logger.info("✅ ngrok tunnel stopped")
        return True
    except Exception as e:
        logger.warning(f"⚠️  ngrok disconnect failed: {e}")
        return False
