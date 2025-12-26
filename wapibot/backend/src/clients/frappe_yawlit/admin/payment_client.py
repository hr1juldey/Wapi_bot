"""Admin payment client stub.

Placeholder for future Frappe payments integration.
Currently uses manual admin API endpoint for payment confirmation.

Future expansion points:
- Listen to Frappe payment webhooks
- Auto-detect payments from Frappe Payments app
- Query payment status from Frappe
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class AdminPaymentClient:
    """Admin payment client for Frappe payments integration (stub).

    Currently a stub for future Frappe payments app integration.
    Manual confirmation via admin_payment_endpoint.py is the primary method.
    """

    def __init__(self, http_client=None):
        """Initialize admin payment client.

        Args:
            http_client: Async HTTP client (for future use)
        """
        self.http = http_client
        logger.info("AdminPaymentClient initialized (stub mode)")

    async def check_frappe_payment(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Check if payment received in Frappe (STUB).

        Future implementation will:
        1. Query Frappe payments table for payment_session_id
        2. Check if payment status is "Paid" or "Captured"
        3. Return payment details if found

        Args:
            session_id: Payment session UUID to check

        Returns:
            Payment details if found in Frappe, None otherwise
        """
        # TODO: Implement Frappe payment lookup
        logger.warning(f"Payment check not implemented yet: {session_id}")
        return None

    async def get_payment_receipt(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get payment receipt from Frappe (STUB).

        Future implementation will fetch payment receipt details
        from Frappe Payments app.

        Args:
            payment_id: Payment ID from Frappe

        Returns:
            Payment receipt details if found
        """
        # TODO: Implement payment receipt fetch
        logger.warning(f"Receipt fetch not implemented yet: {payment_id}")
        return None

    async def setup_webhook(self, webhook_url: str) -> bool:
        """Setup Frappe payment webhook (STUB).

        Future implementation will register webhook for payment updates
        with Frappe Payments app.

        Args:
            webhook_url: URL for Frappe to send payment webhooks

        Returns:
            True if webhook setup successful
        """
        # TODO: Implement webhook registration
        logger.warning(f"Webhook setup not implemented yet: {webhook_url}")
        return False
