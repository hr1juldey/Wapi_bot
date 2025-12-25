"""Workflow state definitions.

Defines the BookingState TypedDict as the single source of truth
for all booking workflow states in LangGraph.
"""

from typing import TypedDict, Optional, Dict, List, Any


class BookingState(TypedDict):
    """Single source of truth for booking workflow state.

    This state is passed through all LangGraph nodes and automatically
    persisted by LangGraph checkpointers.
    """

    # Conversation Context
    conversation_id: str
    user_message: str
    history: List[Dict[str, str]]

    # Extracted Data (replaces scratchpad)
    customer: Optional[Dict[str, Any]]  # {first_name, last_name, phone}
    vehicle: Optional[Dict[str, Any]]   # {brand, model, number_plate}
    appointment: Optional[Dict[str, Any]]  # {date, time_slot, service_type}

    # AI Analysis
    sentiment: Optional[Dict[str, float]]  # {interest, anger, disgust, boredom}
    intent: Optional[str]  # "book", "inquire", "complaint", etc.
    intent_confidence: float

    # Workflow Control
    current_step: str  # Current node name (e.g., "extract_name")
    completeness: float  # 0.0-1.0 data collection progress
    errors: List[str]  # Errors encountered during processing

    # Response Generation
    response: str  # Response message to user
    should_confirm: bool  # Show confirmation screen
    should_proceed: bool  # Continue conversation

    # API Responses (intermediate results from call_frappe nodes)
    customer_lookup_response: Optional[Dict[str, Any]]  # {exists: bool, data: {...}}

    # Booking Result
    service_request_id: Optional[str]  # Created when booking confirmed
    service_request: Optional[Dict[str, Any]]  # Full service request details


# Type alias for cleaner imports
State = BookingState
