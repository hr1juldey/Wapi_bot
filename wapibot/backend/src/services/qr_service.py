"""QR code generation service for UPI payments.

Handles UPI string generation and QR code image creation.
Uses qrcode[pil] library for generation and file storage.
"""

import io
import logging
import qrcode
import urllib.parse
from pathlib import Path
from typing import Optional, Tuple

from core.config import settings

logger = logging.getLogger(__name__)


class QRGenerationService:
    """Service for generating UPI payment QR codes."""

    def __init__(self):
        """Initialize QR service with storage path from config."""
        self.upi_id = settings.upi_id
        self.qr_storage_path = (
            Path(__file__).parent.parent.parent / "data" / "qr_codes"
        )
        self.qr_storage_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"QR storage path: {self.qr_storage_path}")

    def generate_upi_string(
        self,
        amount: Optional[float] = None,
        transaction_note: Optional[str] = None,
    ) -> str:
        """Generate UPI deep link string.

        Format: upi://pay?pa=UPI_ID&am=AMOUNT&cu=INR&tn=NOTE

        Args:
            amount: Optional transaction amount in rupees
            transaction_note: Optional description of transaction

        Returns:
            Complete UPI URI string ready for QR encoding
        """
        upi_string = f"upi://pay?pa={self.upi_id}&cu=INR"

        if amount is not None:
            upi_string += f"&am={amount:.2f}"

        if transaction_note:
            encoded_note = urllib.parse.quote(transaction_note)
            upi_string += f"&tn={encoded_note}"

        logger.debug(f"Generated UPI string: {upi_string}")
        return upi_string

    def generate_qr_image(
        self,
        upi_string: str,
        session_id: str,
        save_to_disk: bool = True,
    ) -> Tuple[bytes, Optional[str]]:
        """Generate QR code image from UPI string.

        Args:
            upi_string: UPI deep link to encode
            session_id: Unique session ID for file naming
            save_to_disk: Whether to save PNG to disk

        Returns:
            Tuple of (PNG bytes, file path if saved to disk)
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(upi_string)
        qr.make(fit=True)

        # Convert to RGB for WAPI compatibility (requires RGB/RGBA, 8-bit/channel)
        img = qr.make_image(fill_color="black", back_color="white").convert('RGB')

        # Convert to PNG bytes
        img_bytes_io = io.BytesIO()
        img.save(img_bytes_io, format="PNG")
        img_bytes = img_bytes_io.getvalue()

        file_path = None
        if save_to_disk:
            file_path = self.qr_storage_path / f"{session_id}.png"
            with open(file_path, "wb") as f:
                f.write(img_bytes)
            logger.info(f"Saved QR code to {file_path}")

        return img_bytes, str(file_path) if file_path else None


# Singleton instance
qr_service = QRGenerationService()
