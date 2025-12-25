"""Workflow state definitions.

Defines the BookingState TypedDict as the single source of truth
for all booking workflow states in LangGraph.
"""

from typing import TypedDict, Optional, Dict, List, Any


class BookingState(TypedDict):
    """Single source of truth for booking workflow state.

    This state is passed through all LangGraph nodes and automatically
    persisted by LangGraph checkpointers.

    IMPORTANT: All fields used in workflows MUST be defined here.
    LangGraph drops undefined fields during state serialization!
    """

    # Conversation Context
    conversation_id: str
    user_message: str
    history: List[Dict[str, str]]

    # Extracted Data (replaces scratchpad)
    customer: Optional[Dict[str, Any]]  # {first_name, last_name, phone, customer_uuid}
    vehicle: Optional[Dict[str, Any]]   # {brand, model, number_plate, vehicle_type}
    appointment: Optional[Dict[str, Any]]  # {date, time_slot, service_type}

    # AI Analysis
    sentiment: Optional[Dict[str, float]]  # {interest, anger, disgust, boredom}
    intent: Optional[str]  # "book", "inquire", "complaint", etc.
    intent_confidence: float

    # Workflow Control
    current_step: str  # Current node name (e.g., "extract_name")
    completeness: float  # 0.0-1.0 data collection progress
    errors: List[str]  # Errors encountered during processing
    gate_decision: Optional[str]  # "high_confidence" or "low_confidence" from confidence_gate

    # Response Generation
    response: str  # Response message to user
    should_confirm: bool  # Show confirmation screen
    should_proceed: bool  # Continue conversation

    # API Responses (intermediate results from API calls)
    customer_lookup_response: Optional[Dict[str, Any]]  # {exists: bool, data: {...}}
    services_response: Optional[Dict[str, Any]]  # Frappe services catalog response
    wapi_response: Optional[Dict[str, Any]]  # WAPI send message response

    # Service Selection
    filtered_services: Optional[List[Dict[str, Any]]]  # Services filtered by vehicle type
    selected_service: Optional[Dict[str, Any]]  # User's selected service
    service_selected: bool  # True if valid service selected
    selection_error: Optional[str]  # Error message for invalid selection

    # Slot Selection
    available_slots: Optional[List[Dict[str, Any]]]  # Available appointment slots
    formatted_slots: Optional[str]  # Human-readable slot options
    slot_selected: bool  # True if valid slot selected

    # Pricing & Confirmation
    total_price: Optional[float]  # Calculated total price
    confirmed: Optional[bool]  # True=confirmed, False=cancelled, None=unclear

    # Booking Result
    service_request_id: Optional[str]  # Created when booking confirmed
    service_request: Optional[Dict[str, Any]]  # Full service request details


# Type alias for cleaner imports
State = BookingState
