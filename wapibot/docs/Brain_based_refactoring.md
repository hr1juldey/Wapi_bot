# Bottom-Up Brain Integration: Proper Architecture

## Problem Summary

1. **Extraction fails with extra context words** - "I want to book on 29th december morning" fails
2. **Brain toggle system is ORPHANED** - exists but never controls behavior
3. **Node groups have inline logic** - violates SOLID, DRY, 100-line rule
4. **System not built bottom-up** - like electron→atom→molecule→cell→organism

## Existing Node Structure (DISCOVERED)

```tree
src/nodes/
├── atomic/               # Core primitives (11 files)
│   ├── extract.py        # Universal extraction (202 lines - NEEDS brain awareness)
│   ├── send_message.py   # Send WhatsApp (NEEDS brain customization hook)
│   ├── transform.py      # Data transformation
│   └── ...
├── extraction/           # Domain-specific extraction (EXISTS!)
│   ├── extract_name.py   # Name extraction (142 lines - EXCEEDS limit)
│   └── (MISSING: slot_preference, confirmation, utilities)
├── selection/            # Selection handling (EXISTS!)
│   └── generic_handler.py # Reusable selection (86 lines - GOOD)
├── brain/                # Brain nodes (10 files - EXISTS!)
│   ├── personalize_message.py
│   ├── log_decision.py
│   └── ...
├── message_builders/     # Message builders (16+ files)
├── transformers/         # Data transformers (4 files)
└── analysis/             # Analysis nodes (3 files)
```

## Architecture Philosophy

**Blender/ComfyUI/LangGraph Pattern**:

```tree
Layer 1: Atomic Nodes (src/nodes/atomic/)
    ↓ composed into
Layer 2: Domain Nodes (src/nodes/extraction/, src/nodes/selection/, src/nodes/brain/)
    ↓ composed into
Layer 3: Node Groups (src/workflows/node_groups/) ← ONLY wiring, NO logic
    ↓ composed into
Layer 4: Workflows (src/workflows/) ← Full flow composition
```

**Key Principle**: Brain awareness goes in Layer 1 (atomic) and Layer 2 (domain), NOT in node groups.

## Current State (WRONG)

**Node groups contain inline extraction**:

```python
# slot_preference_group.py - 40+ lines of inline extraction
async def extract_preference(state):
    time_result = extract_time_range(message, TIME_RANGE_PATTERNS)  # INLINE!
    date_result = extract_date(message, DATE_PATTERNS)              # INLINE!
    # ... more inline logic
```

**Atomic extract.py exists but is unused**:

```python
# extract.py - 202 lines, battle-tested, UNUSED in booking flow
async def node(state, extractor: Extractor, field_path, fallback_fn=None):
    # Handles timeouts, fallbacks, DSPy execution
```

## Target State (RIGHT)

### Layer 1: Atomic Nodes with Brain Awareness

**`src/nodes/atomic/extract.py`** - Add brain mode awareness:

```python
async def node(
    state: BookingState,
    extractor: Extractor,                    # DSPy extractor
    field_path: str,                         # Where to store result
    fallback_fn: Callable = None,            # Regex fallback
    # NEW: Brain mode control
    respect_brain_mode: bool = True          # Check brain toggles
) -> BookingState:
    """Extraction with brain mode awareness."""
    settings = get_brain_settings() if respect_brain_mode else None

    if settings and settings.brain_mode == "reflex":
        # Reflex: Try fallback FIRST (cheaper)
        if settings.reflex_regex_first and fallback_fn:
            result = fallback_fn(state["user_message"])
            if result:
                return set_field(state, field_path, result)

        # Regex failed - check fail_fast
        if settings.reflex_fail_fast:
            return state  # Don't try DSPy

        # Try DSPy
        return await _run_dspy(state, extractor, field_path)

    elif settings and settings.brain_mode == "conscious":
        # Conscious: DSPy first (quality)
        result = await _run_dspy(state, extractor, field_path)
        if not result and fallback_fn:
            # DSPy failed, try fallback
            return fallback_fn(state["user_message"])
        return result

    else:  # shadow or no settings
        # Current behavior: DSPy first, fallback on failure
        return await _current_behavior(state, extractor, field_path, fallback_fn)
```

**`src/nodes/atomic/send_message.py`** - Add brain customization hook:

```python
async def node(
    state: BookingState,
    message_builder: MessageBuilder,
    # NEW: Brain customization
    allow_brain_customize: bool = True
) -> BookingState:
    """Send message with optional brain customization."""
    message = message_builder(state)

    if allow_brain_customize and can_customize_template():
        # Brain can tweak the message
        message = await brain_customize(message, state)

    return await _send(state, message)
```

### Layer 2: Domain Extraction Nodes (in `src/nodes/extraction/`)

**Pattern from existing `extract_name.py`** (but needs refactoring):

```python
# Currently 142 lines - EXCEEDS 100-line limit
# Currently hardcodes DSPy-first - IGNORES brain mode
# Should use atomic extract.node() internally
```

**Create**: `src/nodes/extraction/extract_slot_preference.py` (~60 lines)

```python
"""Slot preference extraction node."""
from nodes.atomic import extract
from dspy_modules.extractors.slot_preference_extractor import SlotPreferenceExtractor
from fallbacks.pattern_extractors import extract_time_range, extract_date
from fallbacks.enhanced_date_fallback import extract_enhanced_date
from models.extraction_patterns import TIME_RANGE_PATTERNS, DATE_PATTERNS

def regex_fallback(message: str) -> dict:
    """Regex fallback for slot preference."""
    result = {}
    time_result = extract_time_range(message, TIME_RANGE_PATTERNS)
    if time_result:
        result["preferred_time_range"] = time_result.get("preferred_time_range")
    date_result = extract_date(message, DATE_PATTERNS) or extract_enhanced_date(message)
    if date_result:
        result["preferred_date"] = date_result.get("preferred_date")
    return result if result else None

async def node(state, timeout=None):
    """Extract slot preference using atomic node."""
    return await extract.node(
        state,
        extractor=SlotPreferenceExtractor(),
        field_path="slot_preference",
        fallback_fn=regex_fallback,
        respect_brain_mode=True  # Atomic handles brain logic
    )
```

**Create similar in `src/nodes/extraction/`**:

- `extract_confirmation.py` - yes/no extraction
- `extract_utilities.py` - electricity/water yes/no

### Layer 3: Node Groups (ONLY Wiring)

**Refactor `slot_preference_group.py`** - Import from domain nodes:

```python
"""Slot preference collection - COMPOSITION ONLY."""
from langgraph.graph import StateGraph, END
from workflows.shared.state import BookingState
from nodes.extraction.extract_slot_preference import node as extract_slot_preference
from nodes.atomic.send_message import node as send_message_node
from nodes.message_builders.date_preference_prompt import DatePreferencePromptBuilder

async def extract_preference(state: BookingState) -> BookingState:
    """Delegate to domain extraction node."""
    return await extract_slot_preference(state)  # ONE LINE!

async def ask_preference(state: BookingState) -> BookingState:
    """Ask preference using atomic node."""
    result = await send_message_node(state, DatePreferencePromptBuilder())
    result["should_proceed"] = False
    result["current_step"] = "awaiting_preference"
    return result

def create_slot_preference_group() -> StateGraph:
    """Create slot preference group - ONLY wiring."""
    workflow = StateGraph(BookingState)
    workflow.add_node("ask_preference", ask_preference)
    workflow.add_node("extract_preference", extract_preference)
    # ... wiring only
    return workflow.compile()
```

**Note**: `generic_handler.py` in `src/nodes/selection/` already follows this pattern and is REUSABLE across vehicle/service/slot/addon selection.

### Layer 4: Brain Toggles Enhancement

**Update `src/core/brain_toggles.py`**:

```python
def get_extraction_strategy() -> Literal["regex_first", "dspy_first", "both"]:
    """Get extraction order based on brain mode."""
    settings = get_brain_settings()
    if settings.brain_mode == "reflex":
        return "regex_first"
    elif settings.brain_mode == "conscious":
        return "dspy_first"
    return "both"  # shadow mode

def should_try_dspy_after_regex_fail() -> bool:
    """Check if DSPy should be tried after regex fails."""
    settings = get_brain_settings()
    if settings.brain_mode == "reflex":
        return not settings.reflex_fail_fast
    return True  # conscious/shadow always try both
```

## Implementation Steps

### Step 1: Enhance Atomic Extract Node

**File**: `src/nodes/atomic/extract.py` (202 lines → split to ~100 + helper)

- Add `respect_brain_mode` parameter
- Import `get_brain_settings` from `core.brain_config`
- Create helper module `src/nodes/atomic/_extract_brain.py` for brain strategies
- Implement reflex/conscious/shadow extraction strategies

### Step 2: Create Domain Extraction Nodes

**Create in `src/nodes/extraction/`** (directory EXISTS):

- `extract_slot_preference.py` (~60 lines) - date/time extraction
- `extract_confirmation.py` (~40 lines) - yes/no for booking confirmation
- `extract_utilities.py` (~40 lines) - electricity/water yes/no

**Refactor existing**:

- `extract_name.py` (142 → ~60 lines) - use atomic extract.node() internally

### Step 3: Enhance Brain Toggles

**File**: `src/core/brain_toggles.py`

- Add `get_extraction_strategy()` → "regex_first" | "dspy_first" | "both"
- Add `should_try_dspy_after_regex_fail()` → respects `reflex_fail_fast`

### Step 4: Refactor Node Groups (Remove Inline Logic)

**7 files in `src/workflows/node_groups/`**:

| File | Current Problem | Fix |
| ------ | ----------------- | ----- |
| `slot_preference_group.py` | 40+ lines inline extraction | Import from `nodes.extraction.extract_slot_preference` |
| `booking_group.py` | Inline "yes"/"confirm" matching | Import from `nodes.extraction.extract_confirmation` |
| `utilities_group.py` | Inline "yes"/"no" matching | Import from `nodes.extraction.extract_utilities` |
| `addon_group.py` | Inline `re.findall` | Use `nodes.selection.generic_handler` |
| `address_group.py` | Inline `int()` parsing | Use `nodes.selection.generic_handler` |
| `vehicle_group.py` | Inline numeric selection | Use `nodes.selection.generic_handler` |
| `slot_group.py` | Inline numeric selection | Use `nodes.selection.generic_handler` |

### Step 5: Update Environment Configuration

**File**: `.env.txt`

```bash
# Brain Configuration
BRAIN_ENABLED=true
BRAIN_MODE=reflex  # shadow | reflex | conscious
REFLEX_REGEX_FIRST=true
REFLEX_FAIL_FAST=false  # Allow DSPy fallback
REFLEX_TEMPLATE_ONLY=true
```

### Step 6: Test All Brain Modes

- Test `BRAIN_MODE=reflex` - regex first, fail_fast controls DSPy
- Test `BRAIN_MODE=conscious` - DSPy first, regex fallback
- Test `BRAIN_MODE=shadow` - both methods, log comparison

## Files to Create

| File | Lines | Purpose |
| ------ | ------- | --------- |
| `src/nodes/atomic/_extract_brain.py` | ~50 | Brain strategy helpers |
| `src/nodes/extraction/extract_slot_preference.py` | ~60 | Slot preference node |
| `src/nodes/extraction/extract_confirmation.py` | ~40 | Yes/no extraction |
| `src/nodes/extraction/extract_utilities.py` | ~40 | Electricity/water |

## Files to Modify

| File | Current Lines | Changes |
| ------ | --------------- | --------- |
| `src/nodes/atomic/extract.py` | 202 | Add brain mode, extract helpers |
| `src/nodes/extraction/extract_name.py` | 142 | Refactor to use atomic node |
| `src/core/brain_toggles.py` | 58 | Add strategy helpers |
| `slot_preference_group.py` | 237 | Remove inline logic |
| `booking_group.py` | 358 | Remove inline confirmation |
| `utilities_group.py` | ~100 | Remove inline yes/no |
| `addon_group.py` | ~150 | Use generic_handler |
| `address_group.py` | ~100 | Use generic_handler |
| `vehicle_group.py` | ~100 | Use generic_handler |
| `slot_group.py` | 219 | Use generic_handler |
| `.env.txt` | - | Add brain configuration |

## Success Criteria

1. ✅ Atomic `extract.py` has brain mode awareness via `respect_brain_mode` parameter

2. ✅ All node groups under 100 lines (currently 237/358/219 → target <100)

3. ✅ Node groups import from `nodes.extraction/` and `nodes.selection/` (no inline logic)

4. ✅ Brain mode controls extraction order: reflex=regex first, conscious=dspy first

5. ✅ "I want to book on 29th december morning" works in all modes

6. ✅ `reflex_fail_fast=false` enables DSPy fallback after regex fails

7. ✅ Clear logging shows which extraction method was used

8. ✅ Domain extraction nodes in `src/nodes/extraction/` (not inline in groups)

9. ✅ `generic_handler.py` reused across all selection-based groups

## Anti-Patterns to Avoid

❌ **Don't fatten node groups** - Import from `nodes.extraction/` or `nodes.selection/`

❌ **Don't duplicate logic** - Use atomic nodes, don't reimplement

❌ **Don't bypass atomic nodes** - Always use `extract.node()` internally

❌ **Don't hardcode brain behavior** - Always check toggles via helpers

❌ **Don't exceed 100 lines** - Split helpers into private modules (`_helper.py`)

❌ **Don't create new extractors directories** - Use existing `src/nodes/extraction/`

## Execution Priority

### **Phase 1 (Critical - Fixes User's Issue)**

1. Add brain mode to atomic `extract.py`
2. Create `extract_slot_preference.py` in `nodes/extraction/`
3. Refactor `slot_preference_group.py` to use it
4. Test with "I want to book on 29th december morning"

### **Phase 2 (Consistency)**

1. Create `extract_confirmation.py`, `extract_utilities.py`
2. Refactor `booking_group.py`, `utilities_group.py`

#### **Phase 3 (Selection Groups)**

1. Refactor remaining groups to use `generic_handler.py`
2. Reduce all groups to <100 lines

### **Phase 4 (Polish)**

1. Update `.env.txt` with brain config
2. Test all brain modes
3. Optional: Add brain customization to `send_message.py`
