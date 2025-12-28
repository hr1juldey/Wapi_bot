# Refactoring Plan: Clean Line Count, DRY & SOLID

**Date:** 2025-12-27
**Baseline:** 25,197 lines of code (excluding tests)
**Target:** ~20,000 lines (20% reduction)
**Violations:** 62 files over 150 lines, DRY and SOLID issues

---

## Executive Summary

### Current State

- **62 files** exceed 150-line limit (100 implementation + 50 overhead)
- **20** duplicate `validate_` functions (DRY violation)
- **25** duplicate `send_` functions (DRY violation)
- **79** direct state mutations (Dependency Inversion violation)
- **34** inline lambdas instead of Protocols (Open/Closed violation)
- **13 functions** in booking_group.py (Single Responsibility violation)

### Target State

- **0 files** over 150 lines
- **Zero** code duplication
- **100%** SOLID compliance
- **Zero** breaking changes (backward compatible via `__init__.py` re-exports)

### Impact Projection

- **-5,200 lines** of code (20% reduction)
- **-700 lines** from workflows (DRY elimination)
- **-500 lines** from models (schema consolidation)
- **-200 lines** from API endpoints
- **-800 lines** from nodes (consolidation)

---

## Dependency Analysis

### Risk Assessment: 🟢 **LOW RISK**

All priority files have minimal coupling:

```
chat_schemas.py (242 lines)
    ↑
    └── api/v1/chat_endpoint.py [1 dependent]

wapi_client.py (279 lines)
    ↑
    ├── nodes/atomic/send_message.py [CRITICAL]
    ├── tasks/reminder_tasks.py
    ├── tests/unit/test_wapi_demo.py
    └── clients/wapi/__init__.py [RE-EXPORT]
    [4 dependents]

booking_group.py (343 lines)
    ↑
    └── workflows/existing_user_booking.py [1 dependent]

wapi_webhook.py (265 lines)
    ↑
    └── api/router_registry.py [ROUTER ONLY, 1 dependent]
```

**Key Finding:** All files have 1-4 dependents - safe to refactor with `__init__.py` re-exports.

---

## Files Exceeding 150-Line Limit (62 Total)

### Workflows (10 files - HIGHEST PRIORITY)

```
343  workflows/node_groups/booking_group.py
248  workflows/node_groups/addon_group.py
237  workflows/node_groups/slot_preference_group.py
215  workflows/node_groups/address_group.py
208  workflows/existing_user_booking.py
205  workflows/node_groups/slot_group.py
194  workflows/v2_full_workflow.py
178  workflows/node_groups/utilities_group.py
149  workflows/node_groups/service_group.py
143  workflows/node_groups/vehicle_group.py
```

### API Endpoints (5 files - HIGH PRIORITY)

```
265  api/v1/wapi_webhook.py
192  api/v1/ws_chat_endpoint.py
168  api/v1/admin_payment_endpoint.py
156  api/health_api.py (RECENTLY FIXED, still close)
153  api/v1/chat_endpoint.py
```

### Atomic Nodes (10 files - MEDIUM PRIORITY)

```
255  nodes/atomic/call_api.py
237  nodes/atomic/read_model.py
201  nodes/atomic/extract.py
192  nodes/atomic/scan.py
183  nodes/atomic/merge.py
181  nodes/atomic/read_signature.py
166  nodes/atomic/validate.py
164  nodes/atomic/confidence_gate.py
160  nodes/atomic/send_message.py
152  nodes/atomic/call_frappe.py
```

### Schemas/Models (7 files - EASY WINS)

```
242  models/chat_schemas.py
198  models/brain_schemas.py
186  models/vehicle.py
186  models/appointment.py
160  models/customer.py
149  models/admin_payment_schemas.py
143  models/response.py
```

### Frappe API Clients (17 files)

```
262  clients/frappe_yawlit/customer/profile_client.py
251  clients/frappe_yawlit/utils/http_client.py
237  clients/frappe_yawlit/customer/lookup_client.py
... (14 more)
```

---

## SOLID Violations

### 1. Single Responsibility Principle (SRP)

**booking_group.py (343 lines, 13 functions)**
Doing too many things:

- ❌ Price calculation
- ❌ Confirmation handling
- ❌ Booking creation
- ❌ Payment QR generation
- ❌ Reminder scheduling
- ❌ Success/error messaging
- ❌ Workflow routing

**Should be:** 6 separate files

**Other SRP violators:**

- utilities_group.py (extract + validate + send)
- addon_group.py (extract + validate + send)
- address_group.py (extract + validate + send)

### 2. Open/Closed Principle (OCP)

**Hardcoded extractors instead of Protocol pattern:**

```python
# WRONG (booking_group.py lines 41-52)
def extract_price_params(s):  # Hardcoded!
    return {...}

# RIGHT
class PriceParamsExtractor(Protocol):
    def __call__(self, state: BookingState) -> Dict: ...
```

**34 inline lambdas** should be Protocol implementations.

### 3. Dependency Inversion Principle (DIP)

**Direct state mutations everywhere (79 occurrences):**

```python
state["field"] = value  # Violates DIP - depends on concrete dict
```

**Should use:** State manager abstraction

---

## DRY Violations

### Duplicate Function Patterns

- **20** `validate_` functions → should use atomic `validate.node()`
- **25** `send_` functions → should use atomic `send_message.node()`
- **10** `build_` functions → should use message builders

### Duplicate Code in Workflow Groups

- **88** logger calls → needs logging abstraction
- **79** direct state modifications → needs state manager
- **6** try/except blocks → needs error handler decorator

### Entry Router Pattern Duplication

Duplicated across 4+ node groups:

- `route_booking_entry()` in booking_group.py
- `route_service_entry()` in service_group.py
- Similar patterns in addon_group.py, slot_group.py

**Should extract to:** `workflows/node_groups/shared/entry_router.py`
**Savings:** 80+ lines

---

## Refactoring Execution Plan

### Phase 1: Line Count (Split Large Files)

**Safe Order (based on dependency analysis):**

#### 1. chat_schemas.py (242 → 3 files)

**Risk:** 🟢 Lowest (1 dependent)

```
models/chat_schemas/
├── __init__.py           # Re-exports for backward compatibility
├── request_schemas.py    # SimpleContact, SimpleMessage, ChatRequest
├── response_schemas.py   # ChatResponse
└── validators.py         # Extracted validator functions
```

**Migration:**

```python
# OLD import (still works)
from models.chat_schemas import ChatRequest

# NEW import (recommended)
from models.chat_schemas.request_schemas import ChatRequest
```

#### 2. wapi_client.py (279 → 4 files)

**Risk:** 🟢 Low (has `__init__.py`, 4 dependents)

```
clients/wapi/
├── __init__.py           # Re-exports (already exists)
├── wapi_client.py        # Core WAPIClient class (~70 lines)
├── messaging.py          # send_message, send_media (~70 lines)
├── contacts.py           # get_contact (~40 lines)
└── factory.py            # get_wapi_client singleton (~30 lines)
```

**Critical dependent:** `nodes/atomic/send_message.py` (must verify after split)

#### 3. booking_group.py (343 → 6 files)

**Risk:** 🟢 Low (1 dependent)

```
workflows/node_groups/booking_group/
├── __init__.py           # create_booking_group() + re-exports
├── pricing.py            # calculate_price (~60 lines)
├── confirmation.py       # send/extract/route confirmation (~60 lines)
├── booking_creation.py   # create_booking (~60 lines)
├── payment_flow.py       # QR generation + reminders (~60 lines)
└── messaging.py          # success/cancelled/unclear messages (~50 lines)
```

**Dependent:** `workflows/existing_user_booking.py` - verify import

#### 4. wapi_webhook.py (265 → 4 files)

**Risk:** 🟢 Lowest (router registration only)

```
api/v1/wapi_webhook/
├── __init__.py           # Router re-export
├── endpoint.py           # Cleaned up wapi_webhook handler (~70 lines)
├── validation.py         # verify_webhook_signature (~40 lines)
├── state_builder.py      # build_initial_state, resume_state (~80 lines)
└── workflow_loader.py    # get_active_workflow (~30 lines)
```

**Dependent:** `api/router_registry.py` - update import

---

### Phase 2: DRY Elimination

#### 5. Extract Shared Entry Router Pattern

**Files affected:** 4+ node groups
**Lines saved:** 80+

```python
# workflows/node_groups/shared/entry_router.py
def create_entry_router(
    current_step_value: str,
    has_data_check: Callable[[BookingState], bool],
    resume_node: str,
    fresh_node: str
) -> Callable[[BookingState], str]:
    """Factory for entry routing logic."""
    def router(state: BookingState) -> str:
        current_step = state.get("current_step", "")
        has_data = has_data_check(state)

        if current_step == current_step_value and has_data:
            logger.info(f"🔀 Resuming at {resume_node}")
            return resume_node
        else:
            logger.info(f"🔀 Starting fresh at {fresh_node}")
            return fresh_node

    return router
```

#### 6. Replace Inline validate_ Functions

**Target:** 20 functions → use `validate.node()`
**Pattern:**

```python
# BEFORE
async def validate_phone(state):
    phone = state.get("phone")
    if not phone or len(phone) != 10:
        state["errors"].append("Invalid phone")
    return state

# AFTER
await validate.node(state, PhoneValidator(), "phone")
```

#### 7. Replace Inline send_ Functions

**Target:** 25 functions → use `send_message.node()`
**Pattern:**

```python
# BEFORE
async def send_greeting(state):
    message = f"Hi {state['name']}!"
    # ... WAPI call logic ...
    return state

# AFTER
await send_message.node(state, GreetingBuilder())
```

#### 8. Create Error Handler Decorator

**Eliminate:** 6 duplicate try/except blocks

```python
# workflows/shared/decorators.py
def handle_node_errors(fallback_state_key: str = "error"):
    def decorator(func):
        async def wrapper(state):
            try:
                return await func(state)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                state[fallback_state_key] = str(e)
                return state
        return wrapper
    return decorator

# USAGE
@handle_node_errors("booking_error")
async def create_booking(state: BookingState) -> BookingState:
    # ... implementation ...
```

---

### Phase 3: SOLID Compliance

#### 9. Create State Manager Abstraction

**Eliminate:** 79 direct state mutations

```python
# workflows/shared/state_manager.py
class StateManager:
    """Abstraction for state access (DIP compliance)."""

    @staticmethod
    def get_nested(state: BookingState, path: str, default=None):
        """Get nested field: 'customer.first_name'"""
        keys = path.split('.')
        value = state
        for key in keys:
            value = value.get(key, {}) if isinstance(value, dict) else default
        return value if value != {} else default

    @staticmethod
    def set_nested(state: BookingState, path: str, value):
        """Set nested field: 'customer.first_name'"""
        keys = path.split('.')
        current = state
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value

# USAGE
# BEFORE: state["customer"]["first_name"] = "John"
# AFTER:  StateManager.set_nested(state, "customer.first_name", "John")
```

#### 10. Convert Lambdas to Protocol Implementations

**Target:** 34 occurrences

```python
# BEFORE (booking_group.py)
lambda s: s  # Pass-through entry

# AFTER
class PassThroughNode(Protocol):
    def __call__(self, state: BookingState) -> BookingState:
        return state

workflow.add_node("entry", PassThroughNode())
```

---

## Validation & Testing Strategy

### After Each Phase

1. **Run full test suite**

   ```bash
   pytest src/tests/ -v
   ```

2. **Verify imports work**

   ```bash
   python -c "from models.chat_schemas import ChatRequest"
   ```

3. **Test API endpoints**

   ```bash
   curl http://localhost:8000/health/doctor
   ```

4. **Check for circular imports**

   ```bash
   python -m ruff check src/
   ```

5. **Commit changes**

   ```bash
   git add .
   git commit -m "refactor: split chat_schemas.py (Phase 1, Task 1)"
   ```

---

## Timeline

### 4-Day Phased Approach

**Day 1:** Phase 1, Tasks 1-2 (chat_schemas.py, wapi_client.py)
**Day 2:** Phase 1, Tasks 3-4 (booking_group.py, wapi_webhook.py)
**Day 3:** Phase 2, Tasks 5-8 (DRY elimination)
**Day 4:** Phase 3, Tasks 9-10 (SOLID compliance)

---

## Success Metrics

### Before Refactoring

- ✅ 25,197 lines of code
- ❌ 62 files over 150 lines
- ❌ 20 validate_ duplicates
- ❌ 25 send_ duplicates
- ❌ 79 state mutations
- ❌ 34 inline lambdas
- ❌ SOLID violations

### After Refactoring

- ✅ ~20,000 lines of code (20% reduction)
- ✅ 0 files over 150 lines
- ✅ 0 duplicate functions
- ✅ 0 direct state mutations
- ✅ 0 inline lambdas
- ✅ 100% SOLID compliance
- ✅ Zero breaking changes

---

## Risk Mitigation

### Backward Compatibility Strategy

All refactored files maintain `__init__.py` re-exports:

```python
# models/chat_schemas/__init__.py
"""Backward compatibility re-exports."""

from .request_schemas import ChatRequest, SimpleContact, SimpleMessage
from .response_schemas import ChatResponse

__all__ = ["ChatRequest", "SimpleContact", "SimpleMessage", "ChatResponse"]
```

This ensures:

- ✅ Old imports still work: `from models.chat_schemas import ChatRequest`
- ✅ New imports recommended: `from models.chat_schemas.request_schemas import ChatRequest`
- ✅ Zero breaking changes for existing code
- ✅ Gradual migration path

---

## Files to Watch

### Critical Dependencies

These files import from priority refactoring targets and must be verified after each split:

1. `api/v1/chat_endpoint.py` - imports chat_schemas
2. `nodes/atomic/send_message.py` - imports wapi_client [CRITICAL]
3. `workflows/existing_user_booking.py` - imports booking_group
4. `api/router_registry.py` - imports wapi_webhook
5. `tasks/reminder_tasks.py` - imports wapi_client

### Test Files to Update

After splitting, these test files may need import updates:

- `tests/unit/test_wapi_demo.py`
- Any tests importing from refactored files

---

## Rollback Plan

If issues arise during refactoring:

1. **Immediate:** `git revert HEAD`
2. **Per-phase:** `git reset --hard <commit-before-phase>`
3. **All phases:** Restore from baseline commit (tag before refactoring)

**Tag baseline:**

```bash
git tag -a refactor-baseline-2025-12-27 -m "Baseline before SOLID/DRY refactoring"
```

---

## References

- **CLAUDE.md:** 100-line rule, SOLID principles, atomic node pattern
- **Original plan:** `/home/riju279/.claude/plans/sharded-churning-rivest-agent-a949221.md`
- **Agent ID:** a949221 (resume planning agent if needed)

● 📊 COMPREHENSIVE CODEBASE AUDIT REPORT

  1️⃣ LINE COUNT SUMMARY

  ✅ Atomic Nodes (Within Limits)

  | File          | Lines | Status             |
  |---------------|-------|--------------------|
  | checkpoint.py | 92    | ✅ Perfect         |
  | log.py        | 92    | ✅ Perfect         |
  | condition.py  | 101   | ✅ Within limit    |
  | response.py   | 108   | ✅ Within overhead |
  | transform.py  | 136   | ✅ Within overhead |

  ❌ Atomic Nodes (VIOLATIONS - Exceed 150 lines)

  | File               | Lines | Over Limit   |
  |--------------------|-------|--------------|
  | call_frappe.py     | 152   | +2 lines     |
  | send_message.py    | 158   | +8 lines     |
  | confidence_gate.py | 164   | +14 lines    |
  | extract.py         | 177   | +27 lines    |
  | read_signature.py  | 181   | +31 lines    |
  | scan.py            | 192   | +42 lines ⚠️ |

  ❌ Node Groups (ALL EXCEED 150-line limit)

  | File                     | Lines | Status       | Target |
  |--------------------------|-------|--------------|--------|
  | utilities_group.py       | 159   | ❌ +9        | 100    |
  | address_group.py         | 183   | ❌ +33       | 170    |
  | slot_preference_group.py | 201   | ❌ +51       | 120    |
  | slot_group.py            | 218   | ❌ +68       | 120    |
  | addon_group.py           | 230   | ❌ +80       | 140    |
  | booking_group.py         | 360   | ❌ +210 ⚠️⚠️ | 140    |

  2️⃣ DRY VIOLATIONS (Code Duplication)

  🔴 CRITICAL: Duplicated Resume Routers (8 files)

  Violation: Each node group has its own route_*_entry() function with identical logic

# Found in: addon_group, address_group, booking_group, service_group

# slot_group, slot_preference_group, utilities_group, vehicle_group

  def route_*_entry(state: BookingState) -> str:
      current_step = state.get("current_step", "")
      # ... same pattern in all files
  Impact: ~160 lines of duplicated code (8 files × ~20 lines)
  Fix: Create reusable resume_router.py (Step 38 - not completed)

  🔴 CRITICAL: Duplicated Error Handlers (6 files)

  Violation: Each selection group has its own send_*_error() function

# Found in: addon_group, address_group, service_group

# slot_group, vehicle_group

  async def send_*_error(state: BookingState) -> BookingState:
      error_msg = state.get("selection_error", "...")
      result = await send_message_node(state, lambda s: error_msg)
      # ... same pattern
  Impact: ~90 lines of duplicated code (6 files × ~15 lines)
  Fix: Create reusable selection_error_handler.py (Step 39 - not completed)

  🟡 MODERATE: Inline Extraction Logic (3 files)

  Violation: addon_group.py, address_group.py, utilities_group.py still have inline extraction

# addon_group.py lines 63-117 (54 lines of inline extraction)

  async def extract_addon_selection(state: BookingState) -> BookingState:
      # Manual parsing, validation, formatting...
  Impact: ~150 lines that should use domain extractors
  Fix: Use atomic extract.node() with domain extractors

  3️⃣ SOLID VIOLATIONS

  ⚠️ Single Responsibility Violations

  booking_group.py (360 lines) - Does TOO MUCH:

- Price calculation
- Confirmation handling
- Booking creation
- Payment QR generation
- Success/error messaging
- Resume routing

  Recommendation: Split into sub-workflows:

- price_calculation_group.py (~80 lines)
- booking_confirmation_group.py (~120 lines)
- payment_flow_group.py (~100 lines)

  ⚠️ Open/Closed Violations

  Inline business logic instead of using Protocols:

# addon_group.py lines 69-75 - Hardcoded keyword matching

  if any(keyword in user_message for keyword in ["none", "skip", "no", "nah"]):
      state["skipped_addons"] = True
  Fix: Use extract.node() with configurable extractor

  4️⃣ BLENDER ARCHITECTURE VIOLATIONS

  🔴 CRITICAL: Node Groups Too Large

  Violation: ALL node groups exceed the 150-line "wiring only" target

  booking_group.py (360 lines) - Should be ~140 lines:

- Has inline price calculation logic (should be domain node)
- Has inline booking params extraction (should be transformer)
- Recommendation: Extract to domain nodes, reduce to ~200 lines

  addon_group.py (230 lines) - Should be ~140 lines:

- 54 lines of inline extraction (lines 63-117)
- Recommendation: Use extract_addon.node(), reduce to ~170 lines

  slot_group.py (218 lines) - Should be ~120 lines:

- Already using transformers ✅
- Excess is mostly from API call overhead
- Acceptable given complexity

  ⚠️ Missing Domain Nodes

  Expected but missing:

- extract_addon.py (Step 31 blocked)
- resume_router.py (Step 38 not done)
- selection_error_handler.py (Step 39 not done)

  5️⃣ COMPLIANCE SUMMARY

  | Principle      | Status     | Violations                    | Impact |
  |----------------|------------|-------------------------------|--------|
  | 100-line limit | 🔴 FAIL    | 6 atomic nodes, 6 node groups | High   |
  | DRY            | 🔴 FAIL    | ~250 lines duplicated         | High   |
  | SOLID - SRP    | 🟡 PARTIAL | booking_group too large       | Medium |
  | SOLID - OCP    | 🟢 PASS    | Using Protocols               | -      |
  | SOLID - DIP    | 🟢 PASS    | Protocol-based design         | -      |
  | Blender        | 🟡 PARTIAL | Node groups too large         | Medium |

  6️⃣ PRIORITY FIXES

  Immediate (High Priority)

  1. ✅ Split booking_group.py (360 → 200 lines)
  - Extract price calculation
  - Extract payment flow
  1. ✅ Refactor addon extraction (230 → 170 lines)
  - Use extract.node() with AddonExtractor
  1. ✅ Create resume_router.py
  - Eliminate ~160 lines of duplication
  1. ✅ Create selection_error_handler.py
  - Eliminate ~90 lines of duplication

  Secondary (Medium Priority)

  1. ⚠️ Refactor large atomic nodes
  - scan.py (192 → 150 lines)
  - read_signature.py (181 → 150 lines)
  - extract.py (177 → 150 lines)

  Tertiary (Low Priority)

  1. 📝 Document acceptable violations
  - slot_group.py complexity justified
  - Some overhead for error handling acceptable

  📈 PHASE 3 SUCCESS METRICS

  ✅ Achievements:

- Created 4 atomic nodes (393 lines total)
- Refactored 5 message builders (saved ~92 lines)
- Added brain awareness to all atomic nodes
- Established Protocol-based architecture

  ❌ Remaining Work:

- 250 lines of duplicated code (DRY violations)
- 6 node groups exceed line limits
- 6 atomic nodes exceed 150 lines
- 3 missing domain nodes

  Overall Grade: B+ (Good progress, but needs cleanup for production)
