"""QR Code image serving endpoint.

Serves stored QR code images via HTTP for WAPI media messages.
Enables WAPI to fetch QR images from public URLs.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/qr", tags=["QR"])

# QR codes storage path: backend/data/qr_codes/
QR_STORAGE_PATH = Path(__file__).parent.parent.parent.parent / "data" / "qr_codes"


@router.get("/{session_id}.png", response_class=FileResponse)
async def get_qr_image(session_id: str):
    """Serve QR code image by session ID.

    Args:
        session_id: Unique payment session identifier

    Returns:
        PNG image file for the QR code

    Raises:
        HTTPException: 404 if QR image not found

    Example:
        GET /api/v1/qr/abc-123-def.png
        Returns: PNG image binary data
    """
    qr_path = QR_STORAGE_PATH / f"{session_id}.png"

    if not qr_path.exists():
        logger.warning(f"QR image not found: {qr_path}")
        raise HTTPException(status_code=404, detail="QR code not found")

    logger.info(f"Serving QR image: {qr_path}")
    return FileResponse(
        path=qr_path,
        media_type="image/png",
        filename=f"{session_id}.png"
    )
