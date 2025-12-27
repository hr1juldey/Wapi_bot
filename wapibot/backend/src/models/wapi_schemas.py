"""WAPI webhook schemas with examples."""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, Any, Union, List


class WAPIContact(BaseModel):
    """WAPI contact information."""

    status: str = Field(..., examples=["existing"])
    phone_number: str = Field(..., examples=["919876543210"])
    uid: str = Field(..., examples=["contact_abc123"])
    first_name: Optional[str] = Field(None, examples=["Ravi"])
    last_name: Optional[str] = Field(None, examples=["Kumar"])
    email: Optional[str] = Field(None, examples=["ravi@example.com"])
    language_code: Optional[str] = Field(None, examples=["en"])
    country: Optional[str] = Field(None, examples=["india"])


class WAPIMedia(BaseModel):
    """WAPI media attachment."""

    type: str = Field(..., examples=["image"])
    link: str = Field(..., examples=["https://example.com/image.jpg"])
    caption: Optional[str] = Field(None, examples=["My car photo"])
    mime_type: str = Field(..., examples=["image/jpeg"])
    file_name: Optional[str] = Field(None, examples=["car.jpg"])


class WAPIMessage(BaseModel):
    """WAPI message data."""

    whatsapp_business_phone_number_id: str = Field(..., examples=["123456"])
    whatsapp_message_id: str = Field(..., examples=["wamid.abc123"])
    replied_to_whatsapp_message_id: Optional[str] = Field(None)
    is_new_message: bool = Field(..., examples=[True])
    body: Optional[str] = Field(
        None,
        examples=["I want to book a car wash"]
    )
    status: Optional[str] = Field(None)
    media: Optional[Union[WAPIMedia, List]] = None

    @field_validator('media', mode='before')
    @classmethod
    def handle_empty_media(cls, v):
        """Convert empty array to None for media field."""
        if v == [] or v == []:
            return None
        return v


class WAPIWebhookPayload(BaseModel):
    """WAPI incoming webhook payload."""

    contact: WAPIContact
    message: WAPIMessage
    whatsapp_webhook_payload: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Raw WhatsApp webhook data"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "contact": {
                    "status": "existing",
                    "phone_number": "919876543210",
                    "uid": "contact_abc123",
                    "first_name": "Ravi",
                    "last_name": "Kumar",
                    "email": "ravi@example.com",
                    "language_code": "en",
                    "country": "india"
                },
                "message": {
                    "whatsapp_business_phone_number_id": "123456",
                    "whatsapp_message_id": "wamid.abc123",
                    "is_new_message": True,
                    "body": "I want to book a car wash for tomorrow"
                }
            }
        }


class WAPIResponse(BaseModel):
    """Response sent back to WAPI webhook."""

    status: str = Field(default="received", examples=["received"])
    message_id: str = Field(..., examples=["wamid.abc123"])