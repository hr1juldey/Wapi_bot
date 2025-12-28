# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Code Architecture Philosophy

### CRITICAL: File Size Limits (STRICTLY ENFORCED)

**Maximum 100 lines per Python file, with 50-line overhead allowed for:**

- Imports (max 20 lines)
- Module docstring (max 15 lines)
- Type definitions/Protocols (max 15 lines)

**Actual implementation code MUST NOT exceed 100 lines.**

Files currently exceeding limits are TECHNICAL DEBT and must be refactored before modification.

### DRY Principle (Don't Repeat Yourself)

**ONE implementation per concern:**

- ✅ ONE `extract.py` node works with ANY extractor (DSPy, regex, API)
- ✅ ONE `validate.py` node works with ANY Pydantic model
- ✅ ONE `call_api.py` node works with ANY HTTP API
- ❌ NO `extract_name.py`, `extract_vehicle.py`, `extract_date.py` - use configuration instead

**Configuration over duplication:**

```python
# WRONG: Multiple files doing the same thing
nodes/extraction/extract_name.py (150 lines)
nodes/extraction/extract_vehicle.py (150 lines)
nodes/extraction/extract_date.py (150 lines)
# = 450 lines of duplicated extraction logic

# RIGHT: One atomic node + configurations
nodes/atomic/extract.py (100 lines)
dspy_modules/extractors/name_extractor.py (40 lines)
dspy_modules/extractors/vehicle_extractor.py (40 lines)
dspy_modules/extractors/date_extractor.py (40 lines)
# = 220 lines total (51% reduction) + reusable
```

### SOLID Principles (STRICTLY ENFORCED)

1. **Single Responsibility**: Each node does ONE thing
   - `extract.py` - ONLY extracts data (doesn't validate, send messages, or call APIs)
   - `validate.py` - ONLY validates (doesn't extract or transform)
   - `send_message.py` - ONLY sends messages (doesn't extract or route)

2. **Open/Closed**: Extend via Protocols, not modification

   ```python
   class Extractor(Protocol):
       def __call__(self, history: list, message: str) -> dict: ...

   # Add new extractor → create new module implementing Protocol
   # NEVER modify extract.py itself
   ```

3. **Liskov Substitution**: Any Protocol implementation must be swappable

   ```python
   # These MUST be interchangeable in extract.node():
   extract.node(state, NameExtractorDSPy(), "customer.first_name")
   extract.node(state, NameExtractorRegex(), "customer.first_name")
   extract.node(state, NameExtractorAPI(), "customer.first_name")
   ```

4. **Interface Segregation**: Minimal Protocol interfaces (one method)
   - `MessageBuilder(Protocol)` has ONE method: `__call__(state) -> str`
   - `Transformer(Protocol)` has ONE method: `__call__(data, state) -> Any`

5. **Dependency Inversion**: Depend on Protocols, not concrete classes
   - Nodes accept Protocol types, not `NameExtractor` or `VehicleExtractor`

### Blender Everything Nodes Architecture (PRIMARY REFERENCE)

**Based on [Blender Geometry Nodes Design (T74967)](https://developer.blender.org/T74967) and [Everything Nodes Architecture](https://devtalk.blender.org/t/blenders-architecture-concerning-everything-nodes/9888)**

This is the CANONICAL design pattern for WapiBot node architecture.

#### 1. Atomic Nodes - Simple, Focused

> "Nodes need to become more atomic, generally simpler" - allowing users to plug in whatever they need

**Applied to WapiBot:**

- `extract.py` is atomic - does ONLY extraction
- `validate.py` is atomic - does ONLY validation
- `send_message.py` is atomic - does ONLY sending
- ❌ **NO Protocol files needed** - just simple, focused nodes
- ❌ **NO `/backend/src/protocols/` directory** - Protocol definitions stay inline in atomic node files

#### 2. Composability is King

> "Creating a group from a single node should have the same behavior as the original node"

**Applied to WapiBot:**

```python
# Node groups are WIRING, not logic
slot_preference_group.py:
    extract.node() → validate.node() → send_message.node()
```

- ✅ Compose atomic nodes in node groups
- ❌ NO separate Protocol abstraction layers
- ❌ NO domain-specific wrapper nodes (like `extract_name.py` that just wraps `extract.node()`)

#### 3. Encapsulation - Dependencies from Outside

> "Geometry nodes systems should be fully encapsulatable, with all dependencies coming from 'outside'"

**Applied to WapiBot:**

```python
# GOOD - dependency injected from outside
await extract.node(state, NameExtractor(), "customer.first_name")

# BAD - hidden dependency
await extract_name.node(state)  # Where does NameExtractor come from?
```

#### 4. Pass-Through Architecture

> "The node will transform only the bits it's concerned with and everything else will be passed through"

**Applied to WapiBot:**

```python
# extract.py only touches extraction field, passes rest of state through
state = await extract.node(state, extractor, "customer.name")
# state still has: history, conversation_id, vehicle, etc. - all passed through
```

#### 5. Generic Inputs > Built-in Properties

> "Properties that were built into modifiers should become generic inputs instead"

**Applied to WapiBot:**

```python
# BAD - built-in property
class ExtractNameNode:
    extractor = NameExtractor()  # Hardcoded!

# GOOD - generic input
await extract.node(state, any_extractor, any_field_path)
```

**References:**

- [Geometry Nodes Design (T74967)](https://developer.blender.org/T74967)
- [Everything Nodes Architecture Discussion](https://devtalk.blender.org/t/blenders-architecture-concerning-everything-nodes/9888)
- [Node Interface Framework](https://developer.blender.org/docs/features/nodes/proposals/node_interface_framework/)
- [Geometry Nodes Workshop Sept 2025](https://code.blender.org/2025/10/geometry-nodes-workshop-september-2025/)

## Atomic Node Architecture

### The 11 Atomic Nodes (Workflow-Level, NOT Code-Level)

**CRITICAL**: These are workflow-level abstractions representing business steps, NOT programming primitives.

1. `extract.py` - Extract data using ANY extractor (DSPy/ReAct/regex/API)
2. `validate.py` - Validate using ANY validator (Pydantic/LLM/custom)
3. `scan.py` - Scan ANY source (history/DB/API)
4. `call_api.py` - Call ANY HTTP API (Yawlit/Frappe/WAPI)
5. `confidence_gate.py` - Gate updates using ANY comparison
6. `merge.py` - Merge data using ANY strategy (confidence/timestamp/LLM)
7. `transform.py` - Transform data using ANY transformer (filter/format/calculate)
8. `condition.py` - Route workflow using ANY predicate
9. `response.py` - Generate response using ANY generator (template/LLM/hybrid)
10. `log.py` - Log using ANY logger (structured/metrics)
11. `checkpoint.py` - Persist state at ANY trigger (milestone/error)

**Current status**: Items 1-6 implemented. Items 7-11 are planned (see `docs/ATOMIC_NODES_REDESIGN_PLAN.md`).

### Protocol Pattern (Standard for ALL Atomic Nodes)

```python
# ALL atomic nodes follow this pattern:
from typing import Protocol

class ThingDoer(Protocol):
    """Protocol defines the interface."""
    def __call__(self, **kwargs) -> ResultType:
        """Do the thing."""
        ...

async def node(
    state: BookingState,
    thing_doer: ThingDoer,  # ← Accepts ANY implementation
    config_param: str,       # ← Configuration, not hardcoding
    **options
) -> BookingState:
    """Atomic node - works with ANY ThingDoer implementation."""
    result = thing_doer(**prepare_inputs(state))
    update_state(state, result, config_param)
    return state
```

### Workflow Composition (NOT Code-Level Noding)

**WRONG** - Code-level nodes (visual programming hell):

```python
[Get Message] → [Create Signature] → [Configure Fields] → [Instantiate Module]
→ [Call Module] → [Parse Result] → [Check None] → [Create Fallback] → [Regex Match]
→ [Extract Groups] → [Convert Dict] → [Validate] → [Store State]
# 13 nodes doing what should be ONE workflow step!
```

**RIGHT** - Workflow-level nodes (business logic abstraction):

```python
[Extract Name] → [Validate Name] → [Check Confidence] → [Generate Response]
# 4 nodes representing 4 business steps
# DSPy complexity is HIDDEN inside extract.node()
```

### Sub-Workflows for Complex Steps

#### **NEVER create `schedule_appointment.py` as a single large node.**

#### **DO create a sub-workflow**: composed from atomic nodes as nodegroups in [node_groups](backend/src/workflows/node_groups/) folder

```python
def create_schedule_appointment_workflow():
    """Sub-workflow: reusable across marketing AND direct booking."""
    workflow = StateGraph(BookingState)

    workflow.add_node("extract_datetime",
        lambda s: extract.node(s, DateTimeExtractor(), "appointment.requested"))
    workflow.add_node("fetch_slots",
        lambda s: call_api.node(s, get_slots_request, "available_slots"))
    workflow.add_node("present_slots",
        lambda s: send_message.node(s, format_slot_options))
    workflow.add_node("capture_selection",
        lambda s: extract.node(s, SlotExtractor(), "appointment.selected"))
    workflow.add_node("validate_slot",
        lambda s: validate.node(s, AppointmentSlot, "appointment"))

    return workflow.compile()
```

## Development Commands

### Start Backend

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

### Run All Tests

```bash
pytest src/tests/
```

### Run Single Test File

```bash
pytest src/tests/unit/test_extract_node.py -v
```

### Run Single Test Function

```bash
pytest src/tests/unit/test_extract_node.py::test_extract_with_dspy_success -v
```

### Type Checking (REQUIRED before commit)

```bash
python -m ruff check src/
```

### Code Quality Check

```bash
python -m pyrefly check src/
```

### Run Frontend Integration Tests

```bash
pytest src/tests/test_frontend/ -v
```

### Launch LangGraph Studio (Visual Workflow Editor)

```bash
langgraph-studio
```

## BookingState: Single Source of Truth

**ALL workflow state lives in `BookingState` TypedDict** (`src/workflows/shared/state.py`).

**NO hidden state, NO globals, NO class attributes.**

```python
class BookingState(TypedDict):
    # Conversation Context
    conversation_id: str
    user_message: str
    history: List[Dict[str, str]]

    # Extracted Data (NOT scratchpad - this IS the data)
    customer: Optional[Dict[str, Any]]   # {first_name, last_name, phone, confidence}
    vehicle: Optional[Dict[str, Any]]    # {brand, model, number_plate, confidence}
    appointment: Optional[Dict[str, Any]] # {date, time_slot, service_type}

    # Workflow Control
    current_step: str
    completeness: float
    errors: List[str]

    # Response
    response: str
    should_confirm: bool
```

**Nested field access** uses dot notation:

```python
# Get nested fields
get_nested_field(state, "customer.first_name")
get_nested_field(state, "vehicle.brand")

# Set nested fields
set_nested_field(state, "customer.first_name", "Rahul")
set_nested_field(state, "appointment.date", "2025-12-25")
```

## Layer Responsibilities

### API Layer (`src/api/v1/`)

- HTTP request/response only
- Pydantic schema validation
- Delegate to service layer
- NO business logic

### Service Layer (`src/services/`)

- Workflow orchestration
- External API coordination
- Transaction management
- NO node implementation

### Workflow Layer (`src/workflows/`)

- LangGraph StateGraph definitions
- Node composition
- Routing logic
- Automatic checkpointing

### Node Layer (`src/nodes/atomic/`)

- Atomic operations (extract, validate, call_api, etc.)
- Protocol-based design
- Single responsibility
- 100-line limit

### DSPy Layer (`src/dspy_modules/`, `src/dspy_signatures/`)

- LLM module implementations
- Signature definitions
- Extractor/analyzer implementations
- Used BY nodes, not calling nodes

### Fallback Layer (`src/fallbacks/`)

- Regex-based fallbacks
- Rule-based extraction
- Used when DSPy fails
- 30-50 lines each

## External Integrations

### WAPI (WhatsApp Business API)

- Client: `src/clients/wapi/`
- Base URL: `https://wapi.in.net`
- Webhook endpoint: `POST /api/v1/wapi/webhook`
- Message sending uses `call_api.node()` with WAPI request builder

### Frappe/Yawlit ERP

- Client: `src/clients/frappe_yawlit/`
- Base URL: Configured via environment
- Modules: customer, booking, payment, subscription, vendor
- All API calls use `call_api.node()` with appropriate request builders

### Frontend (Next.js)

- Development server: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- Chat endpoint: `POST /api/v1/chat`
- Dual format support: Simple format OR WAPI-like format

## Testing Strategy

### Unit Tests

- Test atomic nodes in isolation
- Mock external dependencies (APIs, LLMs)
- Focus on edge cases
- Location: `src/tests/unit/`

### Integration Tests

- Test sub-workflows end-to-end
- Use real state transformations
- Mock only external APIs
- Location: `src/tests/integration/`

### Workflow Tests

- Test complete workflows
- Use LangGraph test harness
- Verify state transitions
- Location: `src/tests/test_workflows/`

## Configuration Files

### `requirements.txt`

Main dependencies - keep minimal, use specific versions for critical deps.

### `pyrefly.toml`

Code quality settings - enforces file inclusion patterns.

### `src/core/config.py`

Pydantic Settings for environment configuration.

## Common Pitfalls to Avoid

### 1. Creating Domain-Specific Nodes

❌ DON'T: Create `send_template_message.py`, `send_greeting.py`, `send_confirmation.py`
✅ DO: Use `send_message.node(state, template_builder)` with different builders

### 2. Violating Single Responsibility

❌ DON'T: Put validation logic inside extract nodes
✅ DO: Extract → Validate (two separate atomic nodes)

### 3. Hidden State

❌ DON'T: Store data in class attributes or globals
✅ DO: Everything in BookingState

### 4. Code-Level Noding

❌ DON'T: Create nodes for every Python operation
✅ DO: Create workflow-level nodes for business steps

### 5. Exceeding File Size Limits

❌ DON'T: Write 200+ line files
✅ DO: Refactor into sub-modules when approaching 100 lines

### 6. Duplicating Logic

❌ DON'T: Copy-paste retry logic into every API call
✅ DO: Implement retry ONCE in `call_api.node()`

## Migration from V1

If you encounter V1 code (monolithic nodes > 500 lines):

1. DO NOT modify in place
2. Create atomic nodes following the Protocol pattern
3. Compose atomic nodes into sub-workflows
4. Replace V1 node with sub-workflow
5. Mark V1 file for deletion

See `docs/ATOMIC_NODES_REDESIGN_PLAN.md` for detailed migration strategy.

## Documentation

- `docs/V2_NODE_DESIGN_BLENDER_PRINCIPLES.md` - Core design philosophy
- `docs/ATOMIC_NODES_THE_RIGHT_ABSTRACTION.md` - Why workflow-level nodes
- `docs/ATOMIC_NODES_REDESIGN_PLAN.md` - Migration plan for marketing flow
- `docs/TESTING_MULTI_CUSTOMER.md` - Multi-customer testing guide

## Success Metrics

A node is well-designed if:

- ✅ ≤100 lines (excluding 50-line overhead)
- ✅ Single responsibility (does ONE thing)
- ✅ Protocol-based (accepts ANY implementation)
- ✅ Reusable (works for multiple use cases)
- ✅ Testable (can mock dependencies)
- ✅ Composable (works with other atomic nodes)

A workflow is well-designed if:

- ✅ 3-7 nodes (not 20+)
- ✅ Each node represents a business step
- ✅ Clear dataflow (state in → state out)
- ✅ No hidden dependencies
- ✅ Reusable sub-workflows
