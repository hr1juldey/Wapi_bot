# Brain System + Feature Fixes - Implementation Plan

> **Save to repo**: `backend/docs/BRAIN_IMPLEMENTATION_PLAN.md`

## Overview

This plan adds a **Brain System** (MAP-inspired cognitive architecture) that runs **alongside** the existing booking workflow. The Brain:

- **Observes** all conversations (shadow trading)
- **Learns** from outcomes (RL Gym)
- **Dreams** using synthetic data (Ollama-powered)
- **Acts** only when feature toggles allow

**No breaking changes to existing Blender-like node/workflow system.**

---

## Architecture: Brain as Nodes & Node Groups (Blender-Style)

**Everything is a Node. The Brain IS a workflow.**

```bash
┌──────────────────────────────────────────────────────────────────────────────┐
│                    BRAIN = LangGraph Workflow (Same Pattern)                 │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    BRAIN NODE GROUP (node_groups/brain_group.py)        │ │
│  │                                                                         │ │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐ │ │
│  │  │ conflict_   │   │ predict_    │   │ evaluate_   │   │ decompose_  │ │ │
│  │  │ monitor     │──▶│ intent      │──▶│ quality     │──▶│ goals       │ │ │
│  │  │ .node()     │   │ .node()     │   │ .node()     │   │ .node()     │ │ │
│  │  └─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘ │ │
│  │         │                                                      │        │ │
│  │         ▼                                                      ▼        │ │
│  │  ┌───────────────────────────────────────────────────────────────────┐ │ │
│  │  │                    route_brain_action() (Conditional Edge)        │ │ │
│  │  │     Based on: conflict_detected, predicted_intent, quality        │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  │         │                                                              │ │
│  │         ├──▶ "reflex" ──▶ [reflex_group] ──▶ template_only responses  │ │
│  │         │                                                              │ │
│  │         ├──▶ "conscious" ──▶ [conscious_group] ──▶ propose_response   │ │
│  │         │                        │                 .node() + BestOfN   │ │
│  │         │                        ▼                                     │ │
│  │         │              ┌─────────────────┐                            │ │
│  │         │              │ log_decision    │                            │ │
│  │         │              │ .node() (RL)    │                            │ │
│  │         │              └─────────────────┘                            │ │
│  │         │                                                              │ │
│  │         └──▶ "shadow" ──▶ [shadow_group] ──▶ log_only .node()         │ │
│  │                                                                         │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐ │
│  │                    DREAM NODE GROUP (node_groups/dream_group.py)        │ │
│  │     (Runs separately via scheduler, not in conversation flow)          │ │
│  │                                                                         │ │
│  │  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐                   │ │
│  │  │ recall_     │   │ generate_   │   │ apply_      │                   │ │
│  │  │ memories    │──▶│ dreams      │──▶│ learnings   │                   │ │
│  │  │ .node()     │   │ .node()     │   │ .node()     │                   │ │
│  │  └─────────────┘   └─────────────┘   └─────────────┘                   │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ Parallel execution (observe only by default)
                                     ▼
┌──────────────────────────────────────────────────────────────────────────────┐
│                    EXISTING BOOKING WORKFLOW (Unchanged)                     │
│    Profile → Vehicle → Service → [Addon] → Slot → Confirmation → Payment    │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Key Insight: Brain Modules ARE Atomic Nodes

| Brain Concept | Implementation |
|---------------|----------------|

| ConflictMonitor | `nodes/brain/conflict_monitor.py` → `conflict_monitor.node(state, detector)` |
| IntentPredictor | `nodes/brain/intent_predictor.py` → `predict_intent.node(state, predictor)` |
| StateEvaluator | `nodes/brain/state_evaluator.py` → `evaluate_quality.node(state, evaluator)` |
| GoalDecomposer | `nodes/brain/goal_decomposer.py` → `decompose_goals.node(state, decomposer)` |
| ResponseProposer | `nodes/brain/response_proposer.py` → `propose_response.node(state, proposer)` |
| Orchestrator | **NOT a node** → Just conditional edges in `brain_group.py` |
| ReflexMode | `node_groups/reflex_group.py` → sub-workflow |
| ConsciousMode | `node_groups/conscious_group.py` → sub-workflow |
| Dreaming | `node_groups/dream_group.py` → scheduled workflow |
| RL Gym | `nodes/brain/log_decision.py` → atomic node |

---

## Feature Toggles (.env)

```bash
# === BRAIN MASTER CONTROLS ===
BRAIN_ENABLED=true                          # Enable brain observation
BRAIN_MODE=shadow                           # shadow | reflex | conscious

# === MODE DEFINITIONS ===
# shadow: Observe only, log decisions, never act
# reflex: Code dictates LLM (spinal cord mode)
# conscious: LLM dictates code (full brain mode)

# === CONSCIOUS MODE - ACTION TOGGLES (Granular) ===
BRAIN_ACTION_TEMPLATE_CUSTOMIZE=true        # FIRST to enable
BRAIN_ACTION_DATE_CONFIRM=false             # Confirm ambiguous dates
BRAIN_ACTION_ADDON_SUGGEST=false            # Suggest addons
BRAIN_ACTION_QA_ANSWER=false                # Answer off-topic questions
BRAIN_ACTION_BARGAINING_HANDLE=false        # Handle price negotiations
BRAIN_ACTION_ESCALATE_HUMAN=false           # Escalate to human
BRAIN_ACTION_CANCEL_BOOKING=false           # Process cancellations
BRAIN_ACTION_FLOW_RESET=false               # Reset/resume flows
BRAIN_ACTION_DYNAMIC_GRAPH=false            # Create new workflow nodes

# === REFLEX MODE SETTINGS ===
REFLEX_REGEX_FIRST=true                     # Always try regex before LLM
REFLEX_TEMPLATE_ONLY=true                   # Only templated responses
REFLEX_FAIL_FAST=true                       # Fail fast on uncertainty

# === DREAMING SETTINGS ===
DREAM_ENABLED=true                          # Enable dreaming
DREAM_OLLAMA_MODEL=llama3.2                 # Local model for dreams
DREAM_INTERVAL_HOURS=6                      # Dream every N hours
DREAM_MIN_CONVERSATIONS=50                  # Min data before dreaming
DREAM_HALLUCINATION_RATIO=0.2               # 20% creative hallucinations

# === RL GYM SETTINGS ===
RL_GYM_ENABLED=true                         # Enable RL logging
RL_GYM_DB_PATH=brain_gym.db                 # SQLite path
RL_GYM_LOG_ALL=true                         # Log all decisions
RL_GYM_OPTIMIZE_INTERVAL=100                # GEPA optimize after N convos

# === CANCELLATION POLICY ===
CANCELLATION_FREE_HOURS=24                  # Free cancel if >24h away

# === ESCALATION ===
SUPPORT_WHATSAPP_NUMBER=+919876543210       # Human escalation number
```

---

## Brain Modules (DSPy-based)

### 1. ConflictMonitor (ACC-like) - Separate LLM Call

Detects: frustration, confusion, bargaining, off-topic, cancellation intent

### 2. IntentPredictor (OFC-like) - Combined Call

Predicts: next user action, conversation direction

### 3. StateEvaluator (OFC-like) - Combined Call

Evaluates: conversation quality, booking completeness, user satisfaction

### 4. GoalDecomposer (aPFC-like) - Combined Call

Decomposes: user intent into sub-goals, required steps

### 5. ResponseProposer (dlPFC-like) - Separate LLM Call

Proposes: optimal response using BestOfN + Refine pattern

### 6. Orchestrator (Coordinates all modules)

Routes: to appropriate action based on module outputs

---

## File Structure (Everything is Nodes & Workflows)

### Brain Atomic Nodes (`src/nodes/brain/`) - NEW FOLDER

```bash
src/nodes/brain/
├── __init__.py                           # ~15 lines
├── conflict_monitor.py                   # ~55 lines - Atomic node
├── intent_predictor.py                   # ~50 lines - Atomic node
├── state_evaluator.py                    # ~50 lines - Atomic node
├── goal_decomposer.py                    # ~55 lines - Atomic node
├── response_proposer.py                  # ~70 lines - Atomic node + BestOfN
├── log_decision.py                       # ~45 lines - RL logging atomic node
├── recall_memories.py                    # ~50 lines - Dream memory recall
├── generate_dreams.py                    # ~65 lines - Ollama dream generation
└── apply_learnings.py                    # ~55 lines - Apply dream learnings
```

### Brain Node Groups (`src/workflows/node_groups/`) - EXISTING FOLDER

```bash
src/workflows/node_groups/
├── brain_group.py                        # ~95 lines - Main brain workflow
├── reflex_group.py                       # ~70 lines - Code-dictates-LLM mode
├── conscious_group.py                    # ~80 lines - LLM-dictates-code mode
├── shadow_group.py                       # ~45 lines - Observe-only mode
├── dream_group.py                        # ~75 lines - Scheduled dreaming
│
# Feature Fixes (also node groups)
├── addon_group.py                        # ~95 lines - Addon offering
├── qa_group.py                           # ~85 lines - Q&A handling
├── bargaining_group.py                   # ~90 lines - Price negotiation
├── cancellation_group.py                 # ~70 lines - Cancellation policy
├── resume_reset_group.py                 # ~65 lines - Flow reset
└── escalation_group.py                   # ~55 lines - Human escalation
```

### Brain DSPy Signatures (`src/dspy_signatures/brain/`) - NEW SUBFOLDER

```bash
src/dspy_signatures/brain/
├── __init__.py                           # ~10 lines
├── conflict_signature.py                 # ~40 lines
├── intent_prediction_signature.py        # ~35 lines
├── state_evaluation_signature.py         # ~35 lines
├── goal_decomposition_signature.py       # ~40 lines
└── response_proposal_signature.py        # ~45 lines
```

### Brain DSPy Modules (`src/dspy_modules/brain/`) - NEW SUBFOLDER

```bash
src/dspy_modules/brain/
├── __init__.py                           # ~10 lines
├── conflict_detector.py                  # ~50 lines - DSPy ChainOfThought
├── intent_predictor_module.py            # ~45 lines - DSPy Predict
├── quality_evaluator.py                  # ~45 lines - DSPy ChainOfThought
├── goal_decomposer_module.py             # ~50 lines - DSPy ChainOfThought
└── response_generator.py                 # ~60 lines - DSPy BestOfN + Refine
```

### Feature Message Builders (`src/nodes/message_builders/`) - EXISTING FOLDER

```bash
src/nodes/message_builders/
├── date_confirmation.py                  # ~45 lines - "Did you mean Dec 31st?"
├── addon_catalog.py                      # ~55 lines - Addon display
├── bargaining_responses.py               # ~80 lines - 4 response stages
├── resume_prompt.py                      # ~40 lines - Resume/reset choice
├── escalation_message.py                 # ~35 lines - Handoff message
└── qa_response.py                        # ~40 lines - Q&A responses
```

### Enhanced Fallbacks (`src/fallbacks/`) - EXISTING FOLDER

```bash
src/fallbacks/
├── enhanced_date_fallback.py             # ~70 lines - Ordinal dates (31st)
└── ordinal_patterns.py                   # ~45 lines - Pattern configs
```

### Brain Core (`src/core/`) - EXISTING FOLDER

```bash
src/core/
├── brain_config.py                       # ~50 lines - Brain settings from .env
├── brain_router.py                       # ~45 lines - Mode routing logic
└── brain_toggles.py                      # ~35 lines - Feature toggle checks
```

### Brain Data Models (`src/models/`) - EXISTING FOLDER

```bash
src/models/
├── brain_state.py                        # ~45 lines - BrainState TypedDict
├── brain_decision.py                     # ~35 lines - Decision record model
└── dream_config.py                       # ~30 lines - Dream settings model
```

### Brain Database (`src/db/`) - EXISTING FOLDER

```bash
src/db/
├── brain_tables.py                       # ~40 lines - SQLite table definitions
└── brain_migrations.py                   # ~30 lines - Create brain tables
```

### Brain Repository (`src/repositories/`) - EXISTING FOLDER

```bash
src/repositories/
├── brain_decision_repo.py                # ~55 lines - Decision CRUD
├── brain_memory_repo.py                  # ~50 lines - Memory bank CRUD
└── brain_dream_repo.py                   # ~45 lines - Dream learnings CRUD
```

### Brain Celery Tasks (`src/tasks/`) - EXISTING FOLDER

```bash
src/tasks/
├── dream_task.py                         # ~60 lines - Celery task for dreaming
└── gepa_optimization_task.py             # ~55 lines - Celery task for GEPA
```

### Brain Control API (`src/api/v1/`) - NEW ENDPOINTS

```bash
src/api/v1/
├── brain_endpoint.py                     # ~95 lines - Brain control API
│   ├── POST /brain/dream                 # Trigger dream cycle manually
│   ├── POST /brain/train                 # Trigger GEPA optimization
│   ├── GET  /brain/status                # Brain status + metrics
│   ├── GET  /brain/features              # List all feature toggles
│   ├── PUT  /brain/features              # Update feature toggles
│   ├── PUT  /brain/mode                  # Switch brain mode
│   └── GET  /brain/decisions             # List recent decisions (RL Gym)
│
├── brain_schemas.py                      # ~45 lines - Pydantic schemas
│   ├── DreamTriggerRequest               # {force: bool, min_conversations: int}
│   ├── TrainTriggerRequest               # {optimizer: "gepa", num_iterations: int}
│   ├── FeatureToggleUpdate               # {feature_name: str, enabled: bool}
│   ├── BrainModeUpdate                   # {mode: "shadow"|"reflex"|"conscious"}
│   ├── BrainStatusResponse               # {mode, enabled, features, metrics}
│   └── DecisionListResponse              # Paginated decision history
```

### Service Layer for Brain API (`src/services/`) - NEW

```bash
src/services/
├── brain_service.py                      # ~80 lines - Brain control service
│   ├── trigger_dream()                   # Enqueue dream Celery task
│   ├── trigger_training()                # Enqueue GEPA Celery task
│   ├── get_brain_status()                # Aggregate status from DB/env
│   ├── get_feature_toggles()             # Read from DB/env
│   ├── update_feature_toggle()           # Update DB + hot-reload
│   ├── set_brain_mode()                  # Update mode (env or DB)
│   └── get_recent_decisions()            # Query RL Gym DB
```

---

## Data Flow

### Shadow Mode (Default - Learning Only)

```bash
User Message
    ↓
┌─────────────────────┐     ┌─────────────────────┐
│  EXISTING WORKFLOW  │ ←─→ │   BRAIN (SHADOW)    │
│  (Takes Action)     │     │  (Observes & Logs)  │
└─────────────────────┘     └─────────────────────┘
                                     ↓
                            ┌─────────────────────┐
                            │     RL GYM          │
                            │ Log: Brain vs Real  │
                            └─────────────────────┘
```

### Reflex Mode (Code Dictates LLM)

```bash
User Message
    ↓
[Regex Extraction] → Success? → [Template Response]
    ↓ Fail
[Rule Engine] → Match? → [Predefined Action]
    ↓ No Match
[DSPy Extraction] → [Constrained Response]
```

### Conscious Mode (LLM Dictates Code)

```bash
User Message
    ↓
Brain Modules Process (parallel/sequential)
    ↓
Orchestrator Decides Action
    ↓
Check Feature Toggle → Allowed? → Execute via Tools
    ↓ Not Allowed
Fallback to Reflex Mode
```

---

## Brain State (Addition to BookingState)

```python
# src/brain/brain_state.py (~35 lines)
class BrainState(TypedDict):
    # Module Outputs
    conflict_detected: Optional[str]       # "frustration" | "bargaining" | None
    predicted_intent: Optional[str]        # Predicted next action
    conversation_quality: float            # 0.0 - 1.0
    decomposed_goals: List[str]           # Sub-goals
    proposed_response: Optional[str]       # Brain's response

    # Control
    brain_mode: str                        # "shadow" | "reflex" | "conscious"
    action_taken: Optional[str]            # What brain did
    confidence: float                      # Brain's confidence

    # Learning
    brain_decision_id: Optional[str]       # For RL tracking
    dream_applied: bool                    # Was a dream learning applied?
```

---

## Implementation Phases

### **PRIORITY ORDER: Feature Fixes FIRST, then Brain System**

### Phase 1: Feature Fixes - Immediate User-Facing (START HERE)

### **Files: ~12, ~700 lines**

1. Enhanced Date Parsing (ordinal dates, "next Wednesday", confirmation)
   - `src/fallbacks/enhanced_date_fallback.py` (~70 lines)
   - `src/fallbacks/ordinal_patterns.py` (~45 lines)
   - `src/nodes/message_builders/date_confirmation.py` (~45 lines)
   - Modify `src/workflows/node_groups/slot_preference_group.py`

2. Addon Node Group
   - `src/workflows/node_groups/addon_group.py` (~95 lines)
   - `src/nodes/message_builders/addon_catalog.py` (~55 lines)

3. Q&A Support
   - `src/workflows/node_groups/qa_group.py` (~85 lines)
   - `src/nodes/message_builders/qa_response.py` (~40 lines)

4. Bargaining Handler
   - `src/workflows/node_groups/bargaining_group.py` (~90 lines)
   - `src/nodes/message_builders/bargaining_responses.py` (~80 lines)

5. Cancellation Policy
   - `src/workflows/node_groups/cancellation_group.py` (~70 lines)

6. Resume/Reset Flow
   - `src/workflows/node_groups/resume_reset_group.py` (~65 lines)
   - `src/nodes/message_builders/resume_prompt.py` (~40 lines)

7. Human Escalation
   - `src/workflows/node_groups/escalation_group.py` (~55 lines)
   - `src/nodes/message_builders/escalation_message.py` (~35 lines)

### Phase 2: Brain Infrastructure (Files: 22, ~850 lines)

**Core:**
8. `src/core/brain_config.py` - Brain settings from .env
9. `src/core/brain_router.py` - Mode routing logic
10. `src/core/brain_toggles.py` - Feature toggle checks

**Models:**
11. `src/models/brain_state.py` - BrainState TypedDict
12. `src/models/brain_decision.py` - Decision record model
13. `src/models/dream_config.py` - Dream settings model

**Database:**
14. `src/db/brain_tables.py` - SQLite table definitions
15. `src/db/brain_migrations.py` - Create brain tables

**Repositories:**
16. `src/repositories/brain_decision_repo.py` - Decision CRUD
17. `src/repositories/brain_memory_repo.py` - Memory bank CRUD
18. `src/repositories/brain_dream_repo.py` - Dream learnings CRUD

**DSPy Signatures:**
19. `src/dspy_signatures/brain/conflict_signature.py`
20. `src/dspy_signatures/brain/intent_prediction_signature.py`
21. `src/dspy_signatures/brain/state_evaluation_signature.py`
22. `src/dspy_signatures/brain/goal_decomposition_signature.py`
23. `src/dspy_signatures/brain/response_proposal_signature.py`

**Celery Tasks:**
24. `src/tasks/dream_task.py` - Scheduled dreaming
25. `src/tasks/gepa_optimization_task.py` - GEPA optimization

**API Layer (Brain Control):**
26. `src/api/v1/brain_schemas.py` - Pydantic request/response schemas (~45 lines)
27. `src/api/v1/brain_endpoint.py` - Brain control REST API (~95 lines)
28. `src/services/brain_service.py` - Service layer for Brain API (~80 lines)
29. Update `src/api/router_registry.py` - Register brain_router

### Phase 3: Brain DSPy Modules (Files: 5, ~250 lines)

1. `src/dspy_modules/brain/conflict_detector.py`
2. `src/dspy_modules/brain/intent_predictor_module.py`
3. `src/dspy_modules/brain/quality_evaluator.py`
4. `src/dspy_modules/brain/goal_decomposer_module.py`
5. `src/dspy_modules/brain/response_generator.py` (BestOfN + Refine)

### Phase 4: Brain Atomic Nodes (Files: 9, ~500 lines)

1. `src/nodes/brain/__init__.py`
2. `src/nodes/brain/conflict_monitor.py` - node()
3. `src/nodes/brain/intent_predictor.py` - node()
4. `src/nodes/brain/state_evaluator.py` - node()
5. `src/nodes/brain/goal_decomposer.py` - node()
6. `src/nodes/brain/response_proposer.py` - node()
7. `src/nodes/brain/log_decision.py` - node() for RL
8. `src/nodes/brain/recall_memories.py` - node() for dreams
9. `src/nodes/brain/generate_dreams.py` - node() for Ollama

### Phase 5: Brain Node Groups (Files: 5, ~365 lines)

1. `src/workflows/node_groups/brain_group.py` - Main brain workflow
2. `src/workflows/node_groups/reflex_group.py` - Code dictates LLM
3. `src/workflows/node_groups/conscious_group.py` - LLM dictates code
4. `src/workflows/node_groups/shadow_group.py` - Observe only
5. `src/workflows/node_groups/dream_group.py` - Workflow for Celery task

### Phase 6: Integration (Modified Files: 4)

- `src/core/config.py` - Add brain + feature settings
- `src/workflows/shared/state.py` - Add brain state fields
- `src/workflows/existing_user_booking.py` - Wire brain parallel execution
- `src/api/v1/chat_endpoint.py` - Trigger brain alongside workflow

---

## Key Design Principles

### 1. Fail-Fast in Reflex Mode

```python
# BAD - Nested ifs
if condition1:
    if condition2:
        if condition3:
            do_thing()

# GOOD - Fail fast
if not condition1:
    return fallback()
if not condition2:
    return fallback()
if not condition3:
    return fallback()
do_thing()
```

### 2. 100 Lines Per File (Strictly Enforced)

- If approaching 100 lines, split into sub-modules
- Each module has single responsibility

### 3. Protocol-Based Design (SOLID)

```python
class BrainModule(Protocol):
    def process(self, state: BrainState) -> BrainState: ...
    def get_confidence(self) -> float: ...
```

### 4. No Breaking Changes

- Brain runs ALONGSIDE existing workflow
- Feature toggles control ALL brain actions
- Existing workflow remains primary

### 5. DRY - Reuse Existing Atomic Nodes

- Brain uses same `extract.node()`, `send_message.node()`, etc.
- No duplicate implementations

---

## Success Criteria

- [ ] Brain observes all conversations in shadow mode
- [ ] All decisions logged to SQLite (RL Gym)
- [ ] Template customization works when enabled
- [ ] Reflex mode uses regex-first, template-only
- [ ] Conscious mode proposes actions via BestOfN
- [ ] Dreaming generates synthetic data overnight
- [ ] No regression in existing booking flow
- [ ] All files ≤100 lines
- [ ] Feature toggles control granular actions
- [ ] **API: POST /brain/dream triggers dream cycle**
- [ ] **API: POST /brain/train triggers GEPA optimization**
- [ ] **API: GET/PUT /brain/features manages toggles**
- [ ] **API: PUT /brain/mode switches brain modes**
- [ ] **API: GET /brain/status returns brain metrics**

---

## Sources & References

- [MAP Architecture (Nature 2025)](https://pmc.ncbi.nlm.nih.gov/articles/PMC12485071/)
- [GEPA Optimizer](https://dspy.ai/api/optimizers/GEPA/overview/)
- [DSPy Tool Use](https://dspy.ai/tutorials/tool_use/)
- [Language Models Need Sleep](https://openreview.net/forum?id=iiZy6xyVVE)
- [DSPy BestOfN + Refine](https://dspy.ai/tutorials/output_refinement/best-of-n-and-refine/)

---

**Ready for implementation!**
