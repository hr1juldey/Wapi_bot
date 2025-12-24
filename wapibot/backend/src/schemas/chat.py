"""Chat API request/response schemas with examples."""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class ChatRequest(BaseModel):
    """Chat message request from frontend."""

    conversation_id: str = Field(
        ...,
        description="Unique conversation ID (phone number)",
        examples=["919876543210"]
    )
    user_message: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="User's message text",
        examples=["I want to book a car wash for my Honda City tomorrow"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "919876543210",
                "user_message": "I want to book a car wash for my Honda City tomorrow"
            }
        }


class ChatResponse(BaseModel):
    """Chat response with extracted data."""

    message: str = Field(
        ...,
        description="Response message to user",
        examples=["Great! I can help you book a car wash. What's your name?"]
    )
    should_confirm: bool = Field(
        default=False,
        description="Show confirmation screen",
        examples=[False]
    )
    completeness: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Data collection progress (0-1)",
        examples=[0.3]
    )
    extracted_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Extracted booking information",
        examples=[{
            "customer": {"first_name": "Ravi", "phone": "919876543210"},
            "vehicle": {"brand": "Honda", "model": "City"},
            "appointment": None
        }]
    )
    service_request_id: Optional[str] = Field(
        default=None,
        description="Service request ID if booking created",
        examples=["SR-2025-001"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Great! I can help you book a car wash. What's your name?",
                "should_confirm": False,
                "completeness": 0.3,
                "extracted_data": {
                    "customer": {"first_name": "Ravi", "phone": "919876543210"},
                    "vehicle": {"brand": "Honda", "model": "City"},
                    "appointment": None
                },
                "service_request_id": None
            }
        }