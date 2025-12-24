# Phase 2 Missing Files Tree

## Current State Analysis

### ✅ What EXISTS (Complete)

**Pydantic Models** (~800 lines total, all complete!):
```
models/
├── ✅ core.py (87 lines) - ExtractionMetadata, ValidationResult
├── ✅ customer.py (124 lines) - Name, Phone models
├── ✅ vehicle.py (124 lines) - VehicleDetails, VehicleBrand enum
├── ✅ appointment.py (122 lines) - Date, Appointment, TimeSlot
├── ✅ sentiment.py (102 lines) - SentimentScores with decision logic
├── ✅ intent.py (63 lines) - Intent classification
└── ✅ response.py (143 lines) - ChatbotResponse with ALL Phase 2 fields
                                   (includes: scratchpad_completeness,
                                    should_confirm, state, typo_corrections, etc.)
```

**Atomic Nodes** (~1350 lines, architecture complete!):
```
nodes/atomic/
├── ✅ extract.py (220 lines) - Extract ANY data
├── ✅ validate.py (170 lines) - Validate ANY data
├── ✅ scan.py (180 lines) - Retroactive scanning
├── ✅ merge.py (170 lines) - Confidence-based merging
├── ✅ confidence_gate.py (150 lines) - Confidence gating
├── ✅ call_api.py (240 lines) - Generic HTTP API calls
├── ✅ read_signature.py (180 lines) - List DSPy signatures
└── ✅ read_model.py (220 lines) - List Pydantic models
```

**Core Infrastructure**:
```
core/
├── ✅ config.py - Settings (no magic numbers)
├── ✅ dspy_config.py - LLM provider configuration
├── ✅ warmup.py - LLM warmup service
workflows/shared/
└── ✅ state.py - BookingState TypedDict
```

**Fallbacks**:
```
fallbacks/
└── ✅ name_fallback.py - Regex name extraction
```

**Utils**:
```
utils/
└── ✅ history_utils.py - Conversation history utilities
```

---

## ❌ What's MISSING (To Pass Phase 2 Tests)

### 1. DSPy Signatures (6 missing, ~60 lines each)

```
dspy_signatures/
├── extraction/
│   ├── ✅ name_signature.py
│   ├── ❌ phone_signature.py          # Extract phone numbers
│   ├── ❌ vehicle_signature.py        # Extract vehicle brand/model
│   ├── ❌ appointment_signature.py    # Extract date/time/service
│   └── ❌ email_signature.py          # Extract email addresses
├── analysis/
│   ├── ❌ sentiment_signature.py      # Analyze sentiment (5 dimensions)
│   ├── ❌ intent_signature.py         # Classify intent
│   └── ❌ typo_signature.py           # Detect typos and suggest corrections
```

**Each signature** (~60 lines):
- Input fields (conversation_history, user_message, context)
- Output fields (extracted data + confidence + reasoning)
- Docstrings and field descriptions
- Example: `name_signature.py` is 63 lines

---

### 2. DSPy Modules (Extractors) (6 missing, ~70 lines each)

```
dspy_modules/
├── extractors/
│   ├── ✅ name_extractor.py
│   ├── ❌ phone_extractor.py          # PhoneExtractor using ChainOfThought
│   ├── ❌ vehicle_extractor.py        # VehicleExtractor
│   ├── ❌ appointment_extractor.py    # AppointmentExtractor
│   └── ❌ email_extractor.py          # EmailExtractor
├── analyzers/
│   ├── ❌ sentiment_analyzer.py       # SentimentAnalyzer (5 dimensions)
│   ├── ❌ intent_classifier.py        # IntentClassifier
│   └── ❌ typo_detector.py            # TypoDetector
```

**Each extractor/analyzer** (~70 lines):
- dspy.Module subclass
- __init__ with ChainOfThought predictor
- __call__ method (not forward!)
- Confidence mapping
- Error handling

---

### 3. Fallbacks (Regex-based) (4 missing, ~70 lines each)

```
fallbacks/
├── ✅ name_fallback.py
├── ❌ phone_fallback.py               # Regex phone extraction (Indian format)
├── ❌ vehicle_fallback.py             # Regex vehicle brand detection
├── ❌ email_fallback.py               # Regex email extraction
└── ❌ date_fallback.py                # Regex date parsing (relative dates)
```

**Each fallback** (~70 lines):
- Regex patterns for Indian formats
- Stopword filtering
- Normalization logic
- Return dict with extracted data

---

### 4. Database Layer (SQLite State Persistence) (3 files, ~100 lines each)

```
db/
├── ❌ models.py                       # SQLAlchemy ORM models
│                                      # - ConversationState table
│                                      # - ConversationHistory table
│                                      # - VersionedState table
├── ❌ connection.py                   # SQLite connection manager
│                                      # - Create engine
│                                      # - Session factory
│                                      # - Init tables
└── ❌ migrations.py                   # Simple migration system
                                       # - Version tracking
                                       # - Schema updates
```

**db/models.py** (~100 lines):
```python
from sqlalchemy import Column, String, Float, JSON, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class ConversationState(Base):
    """Versioned conversation state storage."""
    __tablename__ = "conversation_states"

    conversation_id = Column(String, primary_key=True)
    version = Column(Integer, primary_key=True)
    state = Column(String)  # "collecting", "confirmation", "completed"
    booking_state = Column(JSON)  # Full BookingState as JSON
    scratchpad_completeness = Column(Float)
    timestamp = Column(DateTime)
    metadata = Column(JSON)

class ConversationHistory(Base):
    """Conversation turn history."""
    __tablename__ = "conversation_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String, index=True)
    turn_number = Column(Integer)
    role = Column(String)  # "user" or "assistant"
    content = Column(String)
    timestamp = Column(DateTime)
    extracted_data = Column(JSON)
```

---

### 5. Repositories (Data Access Layer) (2 files, ~100 lines each)

```
repositories/
├── ❌ conversation_repository.py      # CRUD for conversations
│                                      # - save_state()
│                                      # - get_state()
│                                      # - get_history()
│                                      # - update_completeness()
└── ❌ booking_repository.py           # Service request creation
                                       # - create_service_request()
                                       # - get_service_request()
```

**conversation_repository.py** (~100 lines):
```python
class ConversationRepository:
    """Repository for conversation state persistence."""

    async def save_state(
        self,
        conversation_id: str,
        booking_state: BookingState,
        state: str,
        completeness: float
    ) -> None:
        """Save versioned conversation state."""

    async def get_state(
        self,
        conversation_id: str
    ) -> Optional[BookingState]:
        """Get latest conversation state."""

    async def get_history(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> List[Dict[str, str]]:
        """Get conversation history."""

    async def add_turn(
        self,
        conversation_id: str,
        role: str,
        content: str,
        extracted_data: Optional[Dict] = None
    ) -> None:
        """Add conversation turn."""
```

---

### 6. Services (Business Logic Layer) (5 files, ~100 lines each)

```
services/
├── ❌ extraction_service.py           # Orchestrate all extractions
│                                      # - extract_all_fields()
│                                      # - Uses atomic extract node
│                                      # - Calls all extractors
├── ❌ completeness_service.py         # Calculate scratchpad completeness
│                                      # - calculate_completeness()
│                                      # - Required fields: name, phone, vehicle, service, date
│                                      # - Returns 0-100%
├── ❌ state_machine_service.py        # Manage conversation states
│                                      # - States: collecting → confirmation → completed
│                                      # - transition_state()
│                                      # - should_show_confirmation()
├── ❌ typo_detection_service.py       # Typo detection and correction
│                                      # - detect_typos()
│                                      # - suggest_corrections()
│                                      # - Common mistakes: "confrim", "bokking"
└── ❌ booking_service.py              # Create service requests
                                       # - create_booking()
                                       # - Generate service_request_id
                                       # - Call external APIs
```

**completeness_service.py** (~80 lines):
```python
class CompletenessService:
    """Calculate scratchpad completeness."""

    REQUIRED_FIELDS = {
        "customer.first_name": 20,  # Weight %
        "customer.phone": 20,
        "vehicle.brand": 20,
        "appointment.service_type": 20,
        "appointment.date": 20,
    }

    def calculate_completeness(
        self,
        state: BookingState
    ) -> float:
        """Calculate 0-100% completeness.

        Returns percentage based on filled required fields.
        """
        total_weight = sum(self.REQUIRED_FIELDS.values())
        filled_weight = 0

        for field_path, weight in self.REQUIRED_FIELDS.items():
            value = get_nested_field(state, field_path)
            if value is not None and value != "":
                filled_weight += weight

        return (filled_weight / total_weight) * 100

    def should_show_confirmation(
        self,
        completeness: float
    ) -> bool:
        """Check if ready for confirmation (>= 80%)."""
        return completeness >= 80.0
```

---

### 7. Orchestration Nodes (5 files, ~80-100 lines each)

```
nodes/
├── analysis/
│   ├── ❌ analyze_sentiment.py        # Sentiment analysis node
│   ├── ❌ classify_intent.py          # Intent classification node
│   └── ❌ detect_typos.py             # Typo detection node
├── booking/
│   ├── ❌ calculate_completeness.py   # Completeness calculation node
│   └── ❌ create_booking.py           # Service request creation node
└── responses/
    ├── ❌ generate_response.py        # Response generation node
    └── ❌ suggest_corrections.py      # Typo correction suggestion node
```

**Each orchestration node** (~80 lines):
- Wraps a service
- Implements node(state) -> state signature
- Updates BookingState
- Logs operations
- Error handling

Example: **nodes/booking/calculate_completeness.py**:
```python
async def node(state: BookingState) -> BookingState:
    """Calculate scratchpad completeness.

    Updates state["completeness"] with 0-100% value.
    Updates state["should_confirm"] if completeness >= 80%.
    """
    service = CompletenessService()

    completeness = service.calculate_completeness(state)
    state["completeness"] = completeness / 100.0  # Normalize to 0-1

    # Trigger confirmation if ready
    if service.should_show_confirmation(completeness):
        state["should_confirm"] = True

    logger.info(f"Scratchpad completeness: {completeness}%")
    return state
```

---

### 8. Phase 2 Workflow (1 file, ~150 lines)

```
workflows/
└── ❌ phase2_booking_workflow.py      # Complete Phase 2 flow
                                       # Entry: extract_all_fields
                                       # Then: analyze_sentiment
                                       # Then: classify_intent
                                       # Then: detect_typos
                                       # Then: calculate_completeness
                                       # Gate: completeness >= 80%?
                                       # If yes: show confirmation
                                       # If no: ask for missing data
                                       # End: create_booking
```

**phase2_booking_workflow.py** (~150 lines):
```python
from langgraph.graph import StateGraph, END
from nodes.atomic import extract_node, scan_node, merge_node
from nodes.analysis import analyze_sentiment, classify_intent, detect_typos
from nodes.booking import calculate_completeness, create_booking
from nodes.responses import generate_response

def create_phase2_workflow() -> StateGraph:
    """Phase 2 booking workflow with all features.

    Flow:
        extract_all → sentiment → intent → typo_detect →
        completeness → [gate] → confirmation | ask_more →
        create_booking → END
    """
    workflow = StateGraph(BookingState)

    # Extraction phase
    workflow.add_node("extract_all", extract_all_fields)
    workflow.add_node("scan_missing", scan_missing_fields)
    workflow.add_node("merge_data", merge_extracted_data)

    # Analysis phase
    workflow.add_node("sentiment", analyze_sentiment)
    workflow.add_node("intent", classify_intent)
    workflow.add_node("typo_detect", detect_typos)

    # Completeness check
    workflow.add_node("completeness", calculate_completeness)

    # Response generation
    workflow.add_node("generate_response", generate_response)

    # Booking creation
    workflow.add_node("create_booking", create_booking)

    # Flow
    workflow.set_entry_point("extract_all")
    workflow.add_edge("extract_all", "scan_missing")
    workflow.add_edge("scan_missing", "merge_data")
    workflow.add_edge("merge_data", "sentiment")
    workflow.add_edge("sentiment", "intent")
    workflow.add_edge("intent", "typo_detect")
    workflow.add_edge("typo_detect", "completeness")

    # Conditional: show confirmation or ask for more data
    workflow.add_conditional_edges(
        "completeness",
        lambda s: "confirm" if s.get("should_confirm") else "ask_more",
        {
            "confirm": "generate_response",
            "ask_more": "generate_response"
        }
    )

    workflow.add_edge("generate_response", END)

    return workflow
```

---

### 9. API Endpoints (1 file, ~100 lines)

```
api/v1/
└── ❌ confirmation_endpoint.py        # /api/confirmation endpoint
                                       # Handles: edit, cancel, confirm actions
                                       # Updates conversation state
                                       # Creates service request on confirm
```

**confirmation_endpoint.py** (~100 lines):
```python
@router.post("/api/confirmation")
async def handle_confirmation(
    conversation_id: str,
    user_input: str,
    action: Literal["confirm", "edit", "cancel"]
) -> Dict[str, Any]:
    """Handle confirmation flow actions.

    Actions:
    - confirm: Create service request, mark as completed
    - edit: Parse edit request, update scratchpad, return to collecting
    - cancel: Mark as cancelled, clear scratchpad
    """
    repo = ConversationRepository()

    # Get current state
    state = await repo.get_state(conversation_id)

    if action == "confirm":
        # Create service request
        service = BookingService()
        service_request_id = await service.create_booking(state)

        # Update state
        state["service_request_id"] = service_request_id
        state["state"] = "completed"

        await repo.save_state(conversation_id, state, "completed", 100.0)

        return {
            "message": "Booking confirmed!",
            "service_request_id": service_request_id,
            "state": "completed"
        }

    elif action == "edit":
        # Parse edit request and update fields
        # ... edit logic

    elif action == "cancel":
        # Mark as cancelled
        state["state"] = "cancelled"
        await repo.save_state(conversation_id, state, "cancelled", 0.0)

        return {
            "message": "Booking cancelled",
            "state": "cancelled"
        }
```

---

### 10. Utilities (2 files, ~80 lines each)

```
utils/
├── ✅ history_utils.py
├── ❌ field_utils.py                  # Nested field get/set helpers
│                                      # - get_nested_field()
│                                      # - set_nested_field()
│                                      # - field_exists()
└── ❌ validation_utils.py             # Common validation helpers
                                       # - is_vehicle_brand()
                                       # - is_valid_phone()
                                       # - is_valid_email()
```

---

## Summary Tree (Files to Create)

```
backend/src/
├── dspy_signatures/
│   ├── extraction/
│   │   ├── phone_signature.py         (~60 lines)
│   │   ├── vehicle_signature.py       (~60 lines)
│   │   ├── appointment_signature.py   (~60 lines)
│   │   └── email_signature.py         (~60 lines)
│   └── analysis/
│       ├── sentiment_signature.py     (~60 lines)
│       ├── intent_signature.py        (~60 lines)
│       └── typo_signature.py          (~60 lines)
│
├── dspy_modules/
│   ├── extractors/
│   │   ├── phone_extractor.py         (~70 lines)
│   │   ├── vehicle_extractor.py       (~70 lines)
│   │   ├── appointment_extractor.py   (~70 lines)
│   │   └── email_extractor.py         (~70 lines)
│   └── analyzers/
│       ├── sentiment_analyzer.py      (~70 lines)
│       ├── intent_classifier.py       (~70 lines)
│       └── typo_detector.py           (~70 lines)
│
├── fallbacks/
│   ├── phone_fallback.py              (~70 lines)
│   ├── vehicle_fallback.py            (~70 lines)
│   ├── email_fallback.py              (~70 lines)
│   └── date_fallback.py               (~70 lines)
│
├── db/
│   ├── models.py                      (~100 lines)
│   ├── connection.py                  (~80 lines)
│   └── migrations.py                  (~60 lines)
│
├── repositories/
│   ├── conversation_repository.py     (~100 lines)
│   └── booking_repository.py          (~80 lines)
│
├── services/
│   ├── extraction_service.py          (~100 lines)
│   ├── completeness_service.py        (~80 lines)
│   ├── state_machine_service.py       (~90 lines)
│   ├── typo_detection_service.py      (~70 lines)
│   └── booking_service.py             (~80 lines)
│
├── nodes/
│   ├── analysis/
│   │   ├── analyze_sentiment.py       (~80 lines)
│   │   ├── classify_intent.py         (~80 lines)
│   │   └── detect_typos.py            (~80 lines)
│   ├── booking/
│   │   ├── calculate_completeness.py  (~80 lines)
│   │   └── create_booking.py          (~90 lines)
│   └── responses/
│       ├── generate_response.py       (~90 lines)
│       └── suggest_corrections.py     (~70 lines)
│
├── workflows/
│   └── phase2_booking_workflow.py     (~150 lines)
│
├── api/v1/
│   └── confirmation_endpoint.py       (~100 lines)
│
└── utils/
    ├── field_utils.py                 (~80 lines)
    └── validation_utils.py            (~90 lines)
```

---

## Total Missing Files: 44 files

**By Category**:
- DSPy Signatures: 7 files (~420 lines)
- DSPy Modules: 7 files (~490 lines)
- Fallbacks: 4 files (~280 lines)
- Database: 3 files (~240 lines)
- Repositories: 2 files (~180 lines)
- Services: 5 files (~420 lines)
- Orchestration Nodes: 7 files (~570 lines)
- Workflows: 1 file (~150 lines)
- API Endpoints: 1 file (~100 lines)
- Utilities: 2 files (~170 lines)

**Total Estimated Lines**: ~3,020 lines

**Average per file**: ~69 lines (respects 100-line limit!)

---

## Implementation Order (Priority)

### Phase 1: Core Data Layer (Database + Repositories)
1. db/connection.py - SQLite setup
2. db/models.py - ORM models
3. repositories/conversation_repository.py - State persistence
4. utils/field_utils.py - Field helpers

**Why first**: State persistence is foundation for everything

### Phase 2: Extraction Pipeline (Complete field extraction)
1. dspy_signatures/extraction/* - All extraction signatures
2. dspy_modules/extractors/* - All extractors
3. fallbacks/* - Regex fallbacks
4. services/extraction_service.py - Orchestrate extractions

**Why second**: Need to extract all fields before analysis

### Phase 3: Analysis Pipeline
1. dspy_signatures/analysis/* - Sentiment, intent, typo signatures
2. dspy_modules/analyzers/* - Analyzers
3. nodes/analysis/* - Analysis nodes

**Why third**: Analysis depends on extracted data

### Phase 4: Completeness & State Machine
1. services/completeness_service.py - Calculate % complete
2. services/state_machine_service.py - State transitions
3. nodes/booking/calculate_completeness.py - Completeness node

**Why fourth**: Drives confirmation trigger

### Phase 5: Response & Confirmation
1. services/typo_detection_service.py - Typo suggestions
2. nodes/responses/* - Response generation
3. api/v1/confirmation_endpoint.py - Confirmation API
4. services/booking_service.py - Create bookings

**Why fifth**: Final user-facing layer

### Phase 6: Orchestration Workflow
1. workflows/phase2_booking_workflow.py - Complete Phase 2 flow
2. Update main.py to use Phase 2 workflow

**Why last**: Brings everything together

---

## SOLID & DRY Compliance

### Single Responsibility
- Each file has ONE job
- Services handle business logic
- Repositories handle data access
- Nodes handle workflow steps
- Extractors handle extraction only

### Open/Closed
- Atomic nodes are open for configuration, closed for modification
- New extractors don't change extract.py
- New validators don't change validate.py

### Liskov Substitution
- All extractors implement same protocol
- All repositories implement same interface
- All nodes have same signature: state → state

### Interface Segregation
- Small, focused interfaces
- Extractor protocol: just __call__
- Repository interface: CRUD operations only

### Dependency Inversion
- Services depend on repository interfaces, not concrete implementations
- Nodes depend on service interfaces, not implementations
- Configuration injected, not hardcoded

### DRY (Don't Repeat Yourself)
- Atomic nodes eliminate duplication (ONE extract.py for all extractions)
- Shared utilities (field_utils, validation_utils)
- Base models for common patterns

### 100-Line Limit
- Average file: 69 lines
- Largest files: ~150 lines (workflows only)
- Most files: 60-90 lines
- Single responsibility keeps files small

---

## Notes

1. **No breaking changes**: All new files, no modifications to existing atomic nodes

2. **Incremental development**: Can implement in 6 phases, testing after each

3. **Testable**: Each file is independently testable (unit tests)

4. **Maintainable**: Small files, clear responsibilities, easy to understand

5. **Scalable**: Adding new extractors/analyzers doesn't change core code

6. **Production-ready**: Proper error handling, logging, validation at every layer
