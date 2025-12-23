import httpx
from typing import Dict, Any, List, Optional
from config import FRAPPE_BASE_URL, FRAPPE_API_KEY, FRAPPE_API_SECRET
import logging

logger = logging.getLogger(__name__)

class FrappeClient:
    def __init__(self):
        self.base_url = FRAPPE_BASE_URL
        self.headers = {
            "Authorization": f"token {FRAPPE_API_KEY}:{FRAPPE_API_SECRET}",
            "Content-Type": "application/json"
        }
    
    async def get_filtered_services(self, category: str, frequency_type: str, vehicle_type: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/method/yawlit_automotive_services.api.customer_portal.get_filtered_services"
        params = {"category": category, "frequency_type": frequency_type, "vehicle_type": vehicle_type}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_optional_addons(self, product_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/method/yawlit_automotive_services.api.booking.get_optional_addons"
        params = {"product_id": product_id}
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def get_available_slots(self, date_str: str, product_id: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/method/yawlit_automotive_services.api.booking.get_available_slots_enhanced"
        params = {"date_str": date_str}
        if product_id:
            params["product_id"] = product_id
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, params=params, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def calculate_price(self, product_id: str, addon_ids: List[Dict], electricity_provided: int, 
                            water_provided: int, payment_mode: str) -> Dict[str, Any]:
        url = f"{self.base_url}/api/method/yawlit_automotive_services.api.booking.calculate_booking_price"
        payload = {
            "product_id": product_id,
            "addon_ids": addon_ids,
            "electricity_provided": electricity_provided,
            "water_provided": water_provided,
            "payment_mode": payment_mode
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()
    
    async def create_booking(self, product_id: str, booking_date: str, slot_id: str, vehicle_id: str,
                           electricity_provided: int, water_provided: int, addon_ids: List[Dict],
                           payment_mode: str, payment_screenshot: Optional[str] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/api/method/yawlit_automotive_services.api.booking.create_booking"
        payload = {
            "product_id": product_id,
            "booking_date": booking_date,
            "slot_id": slot_id,
            "vehicle_id": vehicle_id,
            "electricity_provided": electricity_provided,
            "water_provided": water_provided,
            "addon_ids": addon_ids,
            "payment_mode": payment_mode
        }
        if payment_screenshot:
            payload["payment_screenshot"] = payment_screenshot
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=self.headers)
            response.raise_for_status()
            return response.json()

frappe_client = FrappeClient()
