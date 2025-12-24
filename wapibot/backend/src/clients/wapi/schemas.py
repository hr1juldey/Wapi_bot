"""WAPI API request/response schemas."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Literal


class ContactCreate(BaseModel):
    """Contact information for auto-creation."""

    first_name: str = Field(..., examples=["Johan"])
    last_name: Optional[str] = Field(None, examples=["Doe"])
    email: Optional[str] = Field(None, examples=["johndoe@domain.com"])
    country: Optional[str] = Field(None, examples=["india"])
    language_code: Optional[str] = Field(None, examples=["en"])
    groups: Optional[str] = Field(
        None,
        description="Comma-separated group names",
        examples=["group1,group2"]
    )
    custom_fields: Optional[Dict[str, str]] = Field(
        None,
        examples=[{"BDay": "2025-09-04"}]
    )


class SendMessageRequest(BaseModel):
    """Request to send a text message via WAPI."""

    phone_number: str = Field(..., examples=["919876543210"])
    message_body: str = Field(..., examples=["Hello from WapiBot!"])
    from_phone_number_id: Optional[str] = Field(
        None,
        description="Optional phone number ID, uses default if not provided"
    )
    contact: Optional[ContactCreate] = Field(
        None,
        description="Auto-create contact if it doesn't exist"
    )


class SendMediaRequest(BaseModel):
    """Request to send media message via WAPI."""

    phone_number: str = Field(..., examples=["919876543210"])
    media_type: Literal["image", "video", "document"] = Field(
        ...,
        examples=["image"]
    )
    media_url: str = Field(
        ...,
        examples=["https://example.com/image.jpg"]
    )
    caption: Optional[str] = Field(
        None,
        description="Caption for image/video media types"
    )
    file_name: Optional[str] = Field(
        None,
        description="File name for document media type"
    )
    from_phone_number_id: Optional[str] = Field(None)
    contact: Optional[ContactCreate] = Field(None)


class WAPIResponse(BaseModel):
    """Generic response from WAPI API."""

    success: bool = True
    message: Optional[str] = None
    data: Optional[Dict] = None
