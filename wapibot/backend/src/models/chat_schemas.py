"""Chat API request/response schemas with examples."""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any, List
import re


class SimpleContact(BaseModel):
    """Simple contact info for WAPI-like format (frontend testing mode)."""

    phone_number: str = Field(
        ...,
        description="Customer phone number",
        examples=["919876543210"]
    )
    first_name: Optional[str] = Field(
        default=None,
        description="Customer first name",
        examples=["Rahul"]
    )
    last_name: Optional[str] = Field(
        default=None,
        description="Customer last name",
        examples=["Kumar"]
    )
    email: Optional[str] = Field(
        default=None,
        description="Customer email",
        examples=["rahul@example.com"]
    )


class SimpleMessage(BaseModel):
    """Simple message info for WAPI-like format (frontend testing mode)."""

    body: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Message text content",
        examples=["I want to book a car wash"]
    )
    message_id: Optional[str] = Field(
        default=None,
        description="Unique message identifier",
        examples=["frontend_1234567890"]
    )


class ChatRequest(BaseModel):
    """
    Chat message request supporting two formats:

    Format 1 (Simple - for direct API calls):
    {
        "conversation_id": "919876543210",
        "user_message": "Hello",
        "history": [...]
    }

    Format 2 (WAPI-like - for frontend testing):
    {
        "contact": {"phone_number": "919876543210", "first_name": "Rahul"},
        "message": {"body": "Hello", "message_id": "msg123"},
        "history": [...]
    }
    """

    # Format 1 fields (simple)
    conversation_id: Optional[str] = Field(
        default=None,
        min_length=10,
        max_length=20,
        description="Unique conversation ID (phone number)",
        examples=["919876543210"]
    )
    user_message: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=2000,
        description="User's message text",
        examples=["I want to book a car wash for my Honda City tomorrow"]
    )

    # Format 2 fields (WAPI-like)
    contact: Optional[SimpleContact] = Field(
        default=None,
        description="Contact information (WAPI-like format)"
    )
    message: Optional[SimpleMessage] = Field(
        default=None,
        description="Message information (WAPI-like format)"
    )

    # Common field
    history: Optional[List[Dict[str, str]]] = Field(
        default=[],
        description="Conversation history for retroactive scanning",
        examples=[[
            {"role": "user", "content": "Hi, I am Hrijul"},
            {"role": "assistant", "content": "Hello! How can I help?"}
        ]]
    )

    @model_validator(mode='after')
    def validate_format(self):
        """Ensure either simple format OR WAPI-like format is provided (not both)."""
        has_simple = self.conversation_id is not None and self.user_message is not None
        has_wapi = self.contact is not None and self.message is not None

        if not (has_simple or has_wapi):
            raise ValueError(
                "Must provide either (conversation_id + user_message) "
                "OR (contact + message)"
            )

        if has_simple and has_wapi:
            raise ValueError(
                "Cannot mix simple and WAPI formats in same request"
            )

        return self

    @field_validator('conversation_id')
    @classmethod
    def validate_conversation_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate conversation ID format (alphanumeric only)."""
        if v is not None and not re.match(r'^[a-zA-Z0-9]+$', v):
            raise ValueError('conversation_id must contain only alphanumeric characters')
        return v

    @field_validator('history')
    @classmethod
    def validate_history(cls, v: Optional[List[Dict[str, str]]]) -> Optional[List[Dict[str, str]]]:
        """Validate history structure has required keys."""
        if v is None:
            return []

        for idx, msg in enumerate(v):
            if not isinstance(msg, dict):
                raise ValueError(f'history[{idx}] must be a dict')
            if 'role' not in msg:
                raise ValueError(f'history[{idx}] must have "role" key')
            if 'content' not in msg:
                raise ValueError(f'history[{idx}] must have "content" key')
            if msg['role'] not in ('user', 'assistant'):
                raise ValueError(f'history[{idx}] role must be "user" or "assistant"')
            if not isinstance(msg['content'], str):
                raise ValueError(f'history[{idx}] content must be a string')
            if len(msg['content']) > 5000:
                raise ValueError(f'history[{idx}] content exceeds 5000 characters')

        return v

    def get_conversation_id(self) -> str:
        """Extract conversation_id from either format."""
        if self.conversation_id:
            return self.conversation_id
        elif self.contact:
            return self.contact.phone_number
        raise ValueError("No conversation_id found")

    def get_user_message(self) -> str:
        """Extract user message from either format."""
        if self.user_message:
            return self.user_message
        elif self.message:
            return self.message.body
        raise ValueError("No user message found")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "conversation_id": "919876543210",
                    "user_message": "I want to book a car wash for my Honda City tomorrow",
                    "history": []
                },
                {
                    "contact": {
                        "phone_number": "919876543210",
                        "first_name": "Rahul",
                        "last_name": "Kumar"
                    },
                    "message": {
                        "body": "I want to book a car wash",
                        "message_id": "frontend_1234567890"
                    },
                    "history": []
                }
            ]
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