"""WAPI client for WhatsApp messaging via wapi.in.net"""

from clients.wapi.wapi_client import WAPIClient, get_wapi_client
from clients.wapi.schemas import (
    SendMessageRequest,
    SendMediaRequest,
    ContactCreate,
    WAPIResponse
)

__all__ = [
    'WAPIClient',
    'get_wapi_client',
    'SendMessageRequest',
    'SendMediaRequest',
    'ContactCreate',
    'WAPIResponse'
]
