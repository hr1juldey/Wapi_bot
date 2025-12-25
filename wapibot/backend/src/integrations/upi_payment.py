"""UPI Payment QR Code Generator for Yawlit Bookings.

Generates UPI QR codes with fixed amounts using the qrcode library.
No server-side logic needed - pure client-side encoding.
"""

import logging
from typing import Optional, Tuple
from io import BytesIO
from urllib.parse import quote

logger = logging.getLogger(__name__)


class UPIPaymentGenerator:
    """Generate UPI QR codes with fixed amounts for bookings."""

    def __init__(
        self,
        business_upi: str,
        business_name: str = "Yawlit Car Care",
    ):
        """Initialize UPI payment generator.

        Args:
            business_upi: Business UPI ID (e.g., "yawlit@okhdfcbank")
            business_name: Display name for UPI transactions
        """
        if not self.validate_upi_id(business_upi):
            raise ValueError(f"Invalid UPI ID format: {business_upi}")

        self.business_upi = business_upi
        self.business_name = quote(business_name)

    def generate_qr_code(
        self,
        amount: float,
        booking_id: str,
        customer_name: Optional[str] = None,
    ) -> Tuple[Optional[bytes], str]:
        """Generate UPI QR code with fixed amount.

        Args:
            amount: Payment amount in rupees (e.g., 500)
            booking_id: Booking ID for transaction reference
            customer_name: Customer name for transaction note (optional)

        Returns:
            Tuple of (qr_image_bytes, upi_deeplink_string)

        Raises:
            ValueError: If amount is invalid
        """
        # Validate amount
        if amount <= 0:
            raise ValueError(f"Amount must be positive, got {amount}")
        if amount > 100000:  # Max UPI limit
            raise ValueError(f"Amount exceeds UPI limit (₹100,000), got {amount}")

        # Build UPI deep link
        tn_note = quote(f"Booking {booking_id}")
        if customer_name:
            tn_note = quote(f"{customer_name} - {booking_id}")

        upi_deeplink = (
            f"upi://pay?"
            f"pn={self.business_name}&"
            f"pa={self.business_upi}&"
            f"am={int(amount)}&"
            f"tn={tn_note}&"
            f"tr={quote(booking_id)}"
        )

        logger.info(
            f"Generated UPI QR for booking {booking_id}: ₹{amount}",
            extra={"booking_id": booking_id, "amount": amount},
        )

        # Generate QR code image
        qr_image_bytes = self._create_qr_image(upi_deeplink)

        return qr_image_bytes, upi_deeplink

    def _create_qr_image(self, data: str) -> bytes:
        """Create QR code image from data string.

        Args:
            data: Data to encode in QR code (UPI deep link)

        Returns:
            PNG image as bytes
        """
        import qrcode

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")

        img_bytes = BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes.getvalue()

    @staticmethod
    def validate_upi_id(upi_id: str) -> bool:
        """Validate UPI ID format (user@bankname)."""
        import re

        pattern = r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9]{3,}$"
        return bool(re.match(pattern, upi_id))

    @staticmethod
    def get_bank_from_upi(upi_id: str) -> str:
        """Extract bank name from UPI ID."""
        bank_code = upi_id.split("@")[-1]
        bank_map = {
            "okhdfcbank": "HDFC",
            "okaxis": "AXIS",
            "okicici": "ICICI",
            "oksbi": "SBI",
            "okbob": "BOB",
            "okyes": "YES",
            "okpnb": "PNB",
            "okkotak": "KOTAK",
        }
        return bank_map.get(bank_code.lower(), "Unknown")
