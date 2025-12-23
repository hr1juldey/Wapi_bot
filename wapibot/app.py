from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import logging
from config import APP_HOST, APP_PORT, LOG_LEVEL
from wapi_client import wapi_client
from frappe_client import frappe_client

logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

app = FastAPI(title="WAPI Bot")

@app.get("/")
def health():
    return {"status": "healthy"}

@app.post("/")
@app.post("/webhook")
async def webhook(request: Request):
    try:
        data = await request.json()
        logger.info(f"Webhook received: {data}")
        
        phone = data.get("phone_number")
        message = data.get("message_body")
        
        if not phone or not message:
            return JSONResponse({"status": "ignored"})
        
        # Send response via WAPI
        await wapi_client.send_message(phone, f"Received: {message}")
        
        return JSONResponse({"status": "success"})
    except Exception as e:
        logger.error(f"Error: {e}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

if __name__ == "__main__":
    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
