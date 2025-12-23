import os
from dotenv import load_dotenv

load_dotenv()

FRAPPE_BASE_URL = os.getenv("FRAPPE_BASE_URL")
FRAPPE_API_KEY = os.getenv("FRAPPE_API_KEY")
FRAPPE_API_SECRET = os.getenv("FRAPPE_API_SECRET")

WAPI_BASE_URL = os.getenv("WAPI_BASE_URL")
WAPI_VENDOR_UID = os.getenv("WAPI_VENDOR_UID")
WAPI_BEARER_TOKEN = os.getenv("WAPI_BEARER_TOKEN")
WAPI_FROM_PHONE_NUMBER_ID = os.getenv("WAPI_FROM_PHONE_NUMBER_ID")

APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", 8000))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
