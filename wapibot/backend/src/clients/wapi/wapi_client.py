"""WAPI API client for sending WhatsApp messages.

Provides async methods to send text and media messages via WAPI.in.net
"""

import logging
from typing import Optional, Dict, Any
import httpx

from core.config import settings
from clients.wapi.schemas import (
    SendMessageRequest,
    SendMediaRequest,
    WAPIResponse
)

logger = logging.getLogger(__name__)


class WAPIClient:
    """Async client for WAPI.in.net API."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        vendor_uid: Optional[str] = None,
        bearer_token: Optional[str] = None,
        from_phone_number_id: Optional[str] = None
    ):
        """Initialize WAPI client with configuration.

        Args:
            base_url: WAPI base URL (default: from settings)
            vendor_uid: Vendor UID (default: from settings)
            bearer_token: Bearer token (default: from settings)
            from_phone_number_id: Default phone number ID (default: from settings)
        """
        self.base_url = base_url or settings.wapi_base_url
        self.vendor_uid = vendor_uid or settings.wapi_vendor_uid
        self.bearer_token = bearer_token or settings.wapi_bearer_token
        self.from_phone_number_id = from_phone_number_id or settings.wapi_from_phone_number_id

        # Validate required credentials
        if not self.vendor_uid or not self.bearer_token:
            raise ValueError(
                "WAPI credentials not configured. "
                "Set WAPI_VENDOR_UID and WAPI_BEARER_TOKEN in .env.txt"
            )

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json"
            }
        )

    async def close(self) -> None:
        """Close HTTP client session."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    def _get_endpoint(self, path: str) -> str:
        """Build endpoint URL with vendor UID.

        Args:
            path: Endpoint path (e.g., "contact/send-message")

        Returns:
            Full endpoint path
        """
        return f"/{self.vendor_uid}/{path}"

    async def send_message(
        self,
        phone_number: str,
        message_body: str,
        from_phone_number_id: Optional[str] = None,
        contact: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send text message via WAPI.

        Args:
            phone_number: Recipient phone number (with country code)
            message_body: Message text content
            from_phone_number_id: Optional phone number ID override
            contact: Optional contact auto-creation data

        Returns:
            API response data

        Raises:
            httpx.HTTPError: Network or API error

        Example:
            >>> client = WAPIClient()
            >>> await client.send_message(
            ...     phone_number="919876543210",
            ...     message_body="Hello from WapiBot!"
            ... )
        """
        payload = {
            "phone_number": phone_number,
            "message_body": message_body
        }

        # Add optional phone number ID
        if from_phone_number_id or self.from_phone_number_id:
            payload["from_phone_number_id"] = from_phone_number_id or self.from_phone_number_id

        # Add optional contact auto-creation
        if contact:
            payload["contact"] = contact

        endpoint = self._get_endpoint("contact/send-message")

        logger.info(f"Sending message to {phone_number}: {message_body[:50]}...")

        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()

            result = response.json() if response.text else {}
            logger.info(f"Message sent successfully to {phone_number}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"Failed to send message to {phone_number}: {e}")
            raise

    async def send_media(
        self,
        phone_number: str,
        media_type: str,
        media_url: str,
        caption: Optional[str] = None,
        file_name: Optional[str] = None,
        from_phone_number_id: Optional[str] = None,
        contact: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Send media message (image, video, document) via WAPI.

        Args:
            phone_number: Recipient phone number
            media_type: Media type (image, video, document)
            media_url: URL to media file
            caption: Caption for image/video
            file_name: File name for document
            from_phone_number_id: Optional phone number ID override
            contact: Optional contact auto-creation data

        Returns:
            API response data

        Raises:
            httpx.HTTPError: Network or API error

        Example:
            >>> await client.send_media(
            ...     phone_number="919876543210",
            ...     media_type="image",
            ...     media_url="https://example.com/car.jpg",
            ...     caption="Your booking confirmation"
            ... )
        """
        payload = {
            "phone_number": phone_number,
            "media_type": media_type,
            "media_url": media_url
        }

        # Add optional fields
        if from_phone_number_id or self.from_phone_number_id:
            payload["from_phone_number_id"] = from_phone_number_id or self.from_phone_number_id

        if caption:
            payload["caption"] = caption

        if file_name:
            payload["file_name"] = file_name

        if contact:
            payload["contact"] = contact

        endpoint = self._get_endpoint("contact/send-media-message")

        logger.info(f"Sending {media_type} to {phone_number}: {media_url}")

        try:
            response = await self.client.post(endpoint, json=payload)
            response.raise_for_status()

            result = response.json() if response.text else {}
            logger.info(f"Media sent successfully to {phone_number}")
            return result

        except httpx.HTTPError as e:
            logger.error(f"Failed to send media to {phone_number}: {e}")
            raise

    async def get_contact(
        self,
        phone_number_or_email: str
    ) -> Optional[Dict[str, Any]]:
        """Get contact information by phone number or email.

        Args:
            phone_number_or_email: Phone number or email address

        Returns:
            Contact data if found, None otherwise

        Example:
            >>> contact = await client.get_contact("919876543210")
        """
        endpoint = self._get_endpoint("contact")
        params = {"phone_number_or_email": phone_number_or_email}

        logger.debug(f"Fetching contact: {phone_number_or_email}")

        try:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()

            result = response.json() if response.text else None
            return result

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.debug(f"Contact not found: {phone_number_or_email}")
                return None
            logger.error(f"Failed to get contact {phone_number_or_email}: {e}")
            raise
        except httpx.HTTPError as e:
            logger.error(f"Failed to get contact {phone_number_or_email}: {e}")
            raise


# Global client instance (lazy initialization)
_wapi_client: Optional[WAPIClient] = None


def get_wapi_client() -> WAPIClient:
    """Get global WAPI client instance.

    Returns:
        Singleton WAPI client

    Example:
        >>> client = get_wapi_client()
        >>> await client.send_message("919876543210", "Hello!")
    """
    global _wapi_client
    if _wapi_client is None:
        _wapi_client = WAPIClient()
    return _wapi_client
