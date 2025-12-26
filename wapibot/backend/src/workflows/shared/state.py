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
    vehicle: Optional[Dict[str, Any]]   # {vehicle_id, vehicle_make, vehicle_model, vehicle_number, vehicle_type}
    appointment: Optional[Dict[str, Any]]  # {date, time_slot, service_type}

    # Profile Validation
    profile_complete: bool  # True if all required profile fields present
    missing_profile_fields: Optional[List[str]]  # List of missing required fields
    addresses: Optional[List[Dict[str, Any]]]  # Customer addresses from profile
    profile_error: Optional[str]  # Error message from profile fetch

    # Vehicle Selection (for multi-vehicle customers)
    vehicle_options: Optional[List[Dict[str, Any]]]  # Available vehicles to choose from
    vehicle_selected: bool  # True if valid vehicle selected
    vehicles_response: Optional[Dict[str, Any]]  # Raw API response from get_vehicles

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
    service_options: Optional[List[Dict[str, Any]]]  # Services available for selection
    selected_service: Optional[Dict[str, Any]]  # User's selected service
    service_selected: bool  # True if valid service selected
    selection_error: Optional[str]  # Error message for invalid selection

    # Slot Selection
    available_slots: Optional[List[Dict[str, Any]]]  # Available appointment slots
    slot_options: Optional[List[Dict[str, Any]]]  # Slots available for selection
    slot: Optional[Dict[str, Any]]  # User's selected slot
    formatted_slots: Optional[str]  # Human-readable slot options
    slot_selected: bool  # True if valid slot selected

    # Slot Preference (Smart Selection)
    preferred_date: Optional[str]  # Preferred date in YYYY-MM-DD format
    preferred_time_range: Optional[str]  # "morning" | "afternoon" | "evening"
    slot_preference_raw: Optional[str]  # Original user message for preference
    slot_preference_extraction_method: Optional[str]  # "regex" | "dspy" | "menu"
    grouped_slots: Optional[Dict[str, List[Dict[str, Any]]]]  # Slots grouped by time of day
    filtered_slot_options: Optional[List[Dict[str, Any]]]  # Filtered slots by preference

    # Pricing & Confirmation
    total_price: Optional[float]  # Calculated total price
    confirmed: Optional[bool]  # True=confirmed, False=cancelled, None=unclear

    # Booking Result
    booking_response: Optional[Dict[str, Any]]  # Response from booking creation API
    service_request_id: Optional[str]  # Created when booking confirmed
    service_request: Optional[Dict[str, Any]]  # Full service request details

    # Payment Fields
    payment_session_id: Optional[str]  # UUID of PaymentSession
    payment_qr_path: Optional[str]  # Path to QR code PNG file
    payment_amount: Optional[float]  # Amount user needs to pay
    payment_confirmed: bool  # True if admin confirmed payment
    payment_status: Optional[str]  # PENDING, CONFIRMED, EXPIRED, CANCELLED
    payment_confirmed_at: Optional[str]  # ISO timestamp of confirmation
    payment_confirmed_by: Optional[str]  # Admin email who confirmed
    payment_reminders_scheduled: Optional[int]  # Number of reminders scheduled


# Type alias for cleaner imports
State = BookingState
