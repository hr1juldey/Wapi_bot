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

    # Address Selection
    selected_address_id: Optional[str]  # Selected address ID for booking
    address_selected: bool  # True if address selected

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

    # Addon Selection
    available_addons: Optional[List[Dict[str, Any]]]  # Addons available for selected service
    selected_addons: Optional[List[Dict[str, Any]]]  # User's selected addons
    addon_ids: Optional[List[str]]  # Selected addon IDs (for API calls)
    addon_selection_complete: bool  # True if user finished addon selection
    skipped_addons: bool  # True if user explicitly skipped addons

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

    # Utilities Collection (for booking_by_phone API)
    electricity_provided: Optional[int]  # 1 (yes) or 0 (no)
    water_provided: Optional[int]  # 1 (yes) or 0 (no)

    # Pricing & Confirmation
    total_price: Optional[float]  # Calculated total price
    price_breakdown: Optional[Dict[str, Any]]  # {base_price, addon_price, discount, tax, total_price}
    discount_code: Optional[str]  # Discount/coupon code (for future promo flow)
    confirmed: Optional[bool]  # True=confirmed, False=cancelled, None=unclear

    # Booking Result
    booking_api_response: Optional[Dict[str, Any]]  # Raw API response from create_booking_by_phone
    booking_response: Optional[Dict[str, Any]]  # Response from booking creation API
    booking_id: Optional[str]  # Booking ID from created booking (e.g., "LIT-BK-HD-OT-291225-0025")
    booking_data: Optional[Dict[str, Any]]  # Full booking data from API response
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

    # Brain System Fields (Phase 2+)
    conflict_detected: Optional[str]  # "frustration" | "bargaining" | "cancellation" | None
    predicted_intent: Optional[str]  # "continue_booking" | "ask_question" | "cancel" etc.
    conversation_quality: float  # 0.0-1.0 quality score
    booking_completeness: float  # 0.0-1.0 booking completion
    user_satisfaction: Optional[float]  # 0.0-1.0 estimated satisfaction
    decomposed_goals: Optional[List[str]]  # Sub-goals from goal decomposer
    required_info: Optional[List[str]]  # Required information identified by brain
    proposed_response: Optional[str]  # Brain's proposed response (conscious mode)
    brain_mode: str  # "shadow" | "reflex" | "conscious"
    action_taken: Optional[str]  # Action brain took (if any)
    brain_confidence: float  # Brain's confidence in decision
    brain_decision_id: Optional[str]  # RL Gym decision ID for tracking
    dream_applied: bool  # Whether a dream learning was applied
    recalled_memories: Optional[List[Dict[str, Any]]]  # Memories for dreaming
    generated_dreams: Optional[List[Dict[str, Any]]]  # Generated dream scenarios
    can_dream: bool  # Whether enough data for dreaming
    dream_status: Optional[str]  # "skipped" | "generated"


# Type alias for cleaner imports
State = BookingState
