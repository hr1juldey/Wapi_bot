import httpx
from typing import Optional, Dict, Any
from config import WAPI_BASE_URL, WAPI_VENDOR_UID, WAPI_BEARER_TOKEN, WAPI_FROM_PHONE_NUMBER_ID
import logging

logger = logging.getLogger(__name__)

class WAPIClient:
    def __init__(self):
        self.base_url = f"{WAPI_BASE_URL}/{WAPI_VENDOR_UID}"
        self.headers = {
            "Authorization": f"Bearer {WAPI_BEARER_TOKEN}",
            "Content-Type": "application/json"
        }
    
    async def send_message(self, phone_number: str, message_body: str) -> Dict[str, Any]:
        url = f"{self.base_url}/contact/send-message"
        payload = {
            "from_phone_number_id": WAPI_FROM_PHONE_NUMBER_ID,
            "phone_number": phone_number,
            "message_body": message_body
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return {"status": "success"}
    
    async def send_interactive_message(self, phone_number: str, body_text: str, buttons: list) -> Dict[str, Any]:
        url = f"{self.base_url}/contact/send-interactive-message"
        payload = {
            "from_phone_number_id": WAPI_FROM_PHONE_NUMBER_ID,
            "phone_number": phone_number,
            "interactive_type": "button",
            "body_text": body_text,
            "buttons": buttons
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return {"status": "success"}

wapi_client = WAPIClient()
