# WapiBot Backend - Intelligent WhatsApp Booking System

## **Production-Ready FastAPI Backend with AI Brain System**

## Overview

WapiBot is an intelligent WhatsApp booking assistant that combines rule-based workflows with a MAP-inspired cognitive architecture. The system handles vehicle service bookings with human-like conversation understanding.

### Key Features

- **Intelligent Booking Flow**: Profile → Vehicle → Service → Addon → Slot → Confirmation → Payment
- **Brain System**: MAP-inspired cognitive architecture with 3 operational modes
- **LLM Resilience**: 3-tier fallback (DSPy → Regex → Ask User)
- **Feature-Rich**: Enhanced date parsing, bargaining, Q&A, cancellation policy, human escalation
- **Visual Workflows**: LangGraph Studio support
- **Type-Safe**: Full Pydantic validation

## Quick Start

### Prerequisites

```bash
# Python 3.12+
python --version

# Install dependencies
uv pip install -r requirements.txt

# Optional: Ollama for dreaming (local LLM)
ollama pull llama3.2
```

### Environment Setup

Create `.env` file in `./` directory:

```bash
# === API Configuration ===
WAPI_URL=https://wapi.in.net
WAPI_API_KEY=your_wapi_key
YAWLIT_URL=https://your-yawlit-instance.com
YAWLIT_API_KEY=your_yawlit_key

# === DSPy Configuration ===
DSPY_LM=ollama/llama3.2
DSPY_API_BASE=http://localhost:11434

# === Brain System ===
BRAIN_ENABLED=true
BRAIN_MODE=shadow

# Brain Action Toggles (Conscious Mode)
BRAIN_ACTION_TEMPLATE_CUSTOMIZE=true
BRAIN_ACTION_DATE_CONFIRM=false
BRAIN_ACTION_ADDON_SUGGEST=false
BRAIN_ACTION_QA_ANSWER=false
BRAIN_ACTION_BARGAINING_HANDLE=false
BRAIN_ACTION_ESCALATE_HUMAN=false
BRAIN_ACTION_CANCEL_BOOKING=false
BRAIN_ACTION_FLOW_RESET=false
BRAIN_ACTION_DYNAMIC_GRAPH=false

# Brain Dreaming
DREAM_ENABLED=true
DREAM_OLLAMA_MODEL=llama3.2
DREAM_INTERVAL_HOURS=6
DREAM_MIN_CONVERSATIONS=50
DREAM_HALLUCINATION_RATIO=0.2

# Brain RL Gym
RL_GYM_ENABLED=true
RL_GYM_DB_PATH=brain_gym.db
RL_GYM_LOG_ALL=true
RL_GYM_OPTIMIZE_INTERVAL=100

# === Feature Configuration ===
CANCELLATION_FREE_HOURS=24
SUPPORT_WHATSAPP_NUMBER=+919876543210
```

### Start the Server

```bash
cd backend
uvicorn src.main:app --reload --port 8000
```

Server will be available at `http://localhost:8000`

### API Docs

- **Swagger UI**: <http://localhost:8000/docs>
- **ReDoc**: <http://localhost:8000/redoc>

## Architecture

### Brain System (MAP-Inspired)

The brain runs **alongside** the booking workflow, observing and learning from conversations.

#### Three Operational Modes

##### **1. Shadow Mode (Default - Production Safe)**

- Observes all conversations without acting
- Logs decisions to RL Gym for learning
- Never interferes with booking flow
- Safe for production deployment

##### **2. Reflex Mode (Code Dictates LLM)**

- Regex-first extraction
- Template-only responses
- Fast, deterministic behavior
- Fail-fast on uncertainty

##### **3. Conscious Mode (LLM Dictates Code)**

- Full brain processing pipeline
- LLM-driven decision making
- Feature toggles control actions
- BestOfN + Refine pattern for responses

#### Brain Modules (DSPy-Based)

- **ConflictMonitor**: Detects frustration, confusion, bargaining
- **IntentPredictor**: Predicts next user action
- **StateEvaluator**: Evaluates conversation quality
- **GoalDecomposer**: Decomposes goals into sub-tasks
- **ResponseProposer**: Proposes optimal responses
- **DreamingSystem**: Generates synthetic training data via Ollama
- **RL Gym**: Logs all decisions for reinforcement learning

### Workflow Architecture

All workflows follow the **Blender Geometry Nodes** philosophy:

- Everything is a node
- Nodes compose into node groups
- Node groups compose into workflows
- Reusable, testable, visual

```bash
User Message
     │
     ├─→ Booking Workflow (main flow)
     │   └─→ Profile → Vehicle → Service → Addon → Slot → Confirmation → Payment
     │
     └─→ Brain Workflow (parallel observation)
         └─→ Shadow/Reflex/Conscious mode → RL Gym logging
```

## Folder Structure

```bash
backend/src/
├── api/v1/                      # FastAPI REST endpoints
│   ├── brain_endpoint.py        # Brain control API
│   ├── wapi_webhook.py          # WhatsApp webhook handler
│   └── router_registry.py       # API router registration
│
├── core/                        # Core configuration
│   ├── config.py                # Main settings
│   ├── brain_config.py          # Brain settings
│   ├── brain_toggles.py         # Feature toggle checks
│   └── brain_router.py          # Brain mode routing
│
├── models/                      # Pydantic data models
│   ├── customer.py              # Customer models
│   ├── vehicle.py               # Vehicle models
│   ├── appointment.py           # Appointment models
│   ├── brain_state.py           # Brain state TypedDict
│   ├── brain_decision.py        # Decision record model
│   └── dream_config.py          # Dream configuration
│
├── workflows/                   # LangGraph workflows
│   ├── existing_user_booking.py # Main booking workflow
│   ├── node_groups/             # Reusable workflow components
│   │   ├── brain_group.py       # Brain orchestrator
│   │   ├── shadow_group.py      # Shadow mode workflow
│   │   ├── reflex_group.py      # Reflex mode workflow
│   │   ├── conscious_group.py   # Conscious mode workflow
│   │   ├── dream_group.py       # Dream workflow
│   │   ├── addon_group.py       # Addon offering
│   │   ├── qa_group.py          # Q&A handling
│   │   ├── bargaining_group.py  # Price negotiation
│   │   ├── cancellation_group.py # Cancellation policy
│   │   ├── resume_reset_group.py # Flow reset
│   │   └── escalation_group.py  # Human escalation
│   └── shared/
│       └── state.py             # BookingState TypedDict
│
├── nodes/                       # Atomic workflow nodes
│   ├── atomic/                  # Reusable atomic nodes
│   │   ├── extract.py           # Data extraction node
│   │   ├── validate.py          # Validation node
│   │   ├── scan.py              # History scanning node
│   │   └── call_api.py          # API calling node
│   ├── brain/                   # Brain processing nodes
│   │   ├── conflict_monitor.py  # Conflict detection
│   │   ├── intent_predictor.py  # Intent prediction
│   │   ├── state_evaluator.py   # Quality evaluation
│   │   ├── goal_decomposer.py   # Goal decomposition
│   │   ├── response_proposer.py # Response proposal
│   │   ├── log_decision.py      # RL logging
│   │   ├── recall_memories.py   # Memory recall
│   │   ├── generate_dreams.py   # Dream generation
│   │   └── apply_learnings.py   # Dream application
│   └── message_builders/        # Message templates
│       ├── date_confirmation.py # Date confirmation prompts
│       ├── addon_catalog.py     # Addon display
│       ├── bargaining_responses.py # Bargaining stages
│       ├── resume_prompt.py     # Resume/reset prompts
│       ├── escalation_message.py # Handoff messages
│       └── qa_response.py       # Q&A responses
│
├── dspy_modules/                # DSPy LLM modules
│   ├── extractors/              # Data extractors
│   └── brain/                   # Brain DSPy modules
│       ├── conflict_detector.py # Conflict detection
│       ├── intent_predictor_module.py # Intent prediction
│       ├── quality_evaluator.py # Quality scoring
│       ├── goal_decomposer_module.py # Goal decomposition
│       └── response_generator.py # Response generation
│
├── dspy_signatures/             # DSPy signatures (I/O specs)
│   ├── extraction/              # Extraction signatures
│   └── brain/                   # Brain signatures
│       ├── conflict_signature.py
│       ├── intent_prediction_signature.py
│       ├── state_evaluation_signature.py
│       ├── goal_decomposition_signature.py
│       └── response_proposal_signature.py
│
├── fallbacks/                   # Regex fallbacks
│   ├── enhanced_date_fallback.py # Ordinal dates + confirmation
│   └── ordinal_patterns.py      # Date pattern configs
│
├── clients/                     # External API clients
│   ├── frappe_yawlit/           # Frappe ERP integration
│   └── wapi/                    # WhatsApp Business API
│
├── db/                          # Database layer
│   ├── brain_tables.py          # Brain table schemas
│   └── brain_migrations.py      # Brain DB migrations
│
├── repositories/                # Data access layer
│   ├── brain_decision_repo.py   # Decision CRUD
│   ├── brain_memory_repo.py     # Memory bank CRUD
│   └── brain_dream_repo.py      # Dream learnings CRUD
│
├── services/                    # Business logic layer
│   └── brain_service.py         # Brain control service
│
├── tasks/                       # Celery background tasks
│   ├── dream_task.py            # Dream cycle task
│   └── gepa_optimization_task.py # GEPA training task
│
└── tests/                       # Test suite
    ├── unit/                    # Unit tests
    ├── integration/             # Integration tests
    └── test_workflows/          # Workflow tests
```

## API Reference

### Brain Control API

**Base URL**: `http://localhost:8000/api/v1/brain`

#### Trigger Dream Cycle

```bash
POST /brain/dream
Content-Type: application/json

{
  "force": false,
  "min_conversations": 50
}

Response:
{
  "task_id": "uuid",
  "status": "queued"
}
```

#### Trigger GEPA Training

```bash
POST /brain/train
Content-Type: application/json

{
  "optimizer": "gepa",
  "num_iterations": 100
}

Response:
{
  "task_id": "uuid",
  "status": "queued"
}
```

#### Get Brain Status

```bash
GET /brain/status

Response:
{
  "enabled": true,
  "mode": "shadow",
  "features": {
    "template_customize": true,
    "date_confirm": false,
    ...
  },
  "metrics": {
    "dream_enabled": true,
    "rl_gym_enabled": true
  }
}
```

#### List Feature Toggles

```bash
GET /brain/features

Response:
{
  "template_customize": true,
  "date_confirm": false,
  "addon_suggest": false,
  ...
}
```

#### Get Recent Decisions

```bash
GET /brain/decisions?limit=100

Response:
[
  {
    "decision_id": "uuid",
    "conversation_id": "uuid",
    "conflict_detected": "bargaining",
    "predicted_intent": "negotiate_price",
    "conversation_quality": 0.75,
    ...
  }
]
```

### WhatsApp Webhook

```bash
POST /api/v1/wapi/webhook
Content-Type: application/json

{
  "event": "message",
  "data": {
    "from": "919876543210",
    "body": "I want to book a service",
    ...
  }
}
```

## Configuration Reference

### Brain Modes

| Mode | Description | Use Case |
|------|-------------|----------|

| `shadow` | Observe only, never act | Production (default) |
| `reflex` | Code dictates LLM | Fast, deterministic responses |
| `conscious` | LLM dictates code | Full AI decision making |

### Feature Toggles (Conscious Mode)

| Toggle | Description | Default |
|--------|-------------|---------|

| `BRAIN_ACTION_TEMPLATE_CUSTOMIZE` | Customize template messages | `true` |
| `BRAIN_ACTION_DATE_CONFIRM` | Confirm ambiguous dates | `false` |
| `BRAIN_ACTION_ADDON_SUGGEST` | Suggest addons | `false` |
| `BRAIN_ACTION_QA_ANSWER` | Answer off-topic questions | `false` |
| `BRAIN_ACTION_BARGAINING_HANDLE` | Handle price negotiations | `false` |
| `BRAIN_ACTION_ESCALATE_HUMAN` | Escalate to human | `false` |
| `BRAIN_ACTION_CANCEL_BOOKING` | Process cancellations | `false` |
| `BRAIN_ACTION_FLOW_RESET` | Reset/resume flows | `false` |
| `BRAIN_ACTION_DYNAMIC_GRAPH` | Create dynamic nodes | `false` |

### Dream System

| Setting | Description | Default |
|---------|-------------|---------|

| `DREAM_ENABLED` | Enable dreaming | `true` |
| `DREAM_OLLAMA_MODEL` | Local model for dreams | `llama3.2` |
| `DREAM_INTERVAL_HOURS` | Dream every N hours | `6` |
| `DREAM_MIN_CONVERSATIONS` | Min data before dreaming | `50` |
| `DREAM_HALLUCINATION_RATIO` | Creative hallucination % | `0.2` |

## Development

### Running Tests

```bash
# All tests
pytest src/tests/

# Unit tests only
pytest src/tests/unit/ -v

# Integration tests
pytest src/tests/integration/ -v

# Specific test
pytest src/tests/unit/test_extract_node.py::test_extract_with_dspy_success -v
```

### Code Quality

```bash
# Linting (required before commit)
python -m ruff check src/

# Auto-fix linting issues
python -m ruff check --fix src/

# Type checking
python -m pyrefly check src/
```

### LangGraph Studio

Visual workflow editor for debugging and testing:

```bash
langgraph-studio
```

Open `http://localhost:8123` to view and debug workflows visually.

### Celery Workers (Background Tasks)

Start Celery worker for dream and training tasks:

```bash
celery -A src.tasks.celery_app worker --loglevel=info
```

## Feature Documentation

### Enhanced Date Parsing

Handles multiple date formats with user confirmation:

- **Ordinal dates**: "31st", "2nd", "21st"
- **Relative dates**: "next Monday", "tomorrow", "this Friday"
- **Ambiguous dates**: Prompts for confirmation ("Did you mean December 31st?")
- **Confidence scoring**: 0.7+ for ordinal-only, 0.85+ for full date

### Addon System

- Shown after service selection
- Multiple selection support
- Skip functionality
- API integration with Yawlit ERP

### Bargaining Handler

4-stage escalation system:

1. **Distract**: Redirect to value proposition
2. **Nudge**: Gentle reminder of fixed pricing
3. **Coupon**: Offer alternative discount
4. **Escalate**: Transfer to human agent

### Cancellation Policy

- Free cancellation if booking >24 hours away
- Charge applies if <24 hours
- Clear policy communication
- Automatic refund processing

### Q&A Support

Answers common questions without breaking booking flow:

- Business hours
- Location information
- Available services
- Pricing information

### Human Escalation

Triggers on:

- Repeated frustration
- Complex requests
- Bargaining failure
- User explicit request

Transfers to WhatsApp support agent with context.

## Code Architecture Principles

### 1. File Size Limits (STRICTLY ENFORCED)

**Maximum 100 lines per Python file** (excluding 50-line overhead for imports/docstrings)

### 2. DRY Principle

ONE implementation per concern:

- ONE `extract.py` node works with ANY extractor
- ONE `validate.py` node works with ANY validator
- ONE `call_api.py` node works with ANY API

### 3. SOLID Principles

- **Single Responsibility**: Each node does ONE thing
- **Open/Closed**: Extend via Protocols, not modification
- **Liskov Substitution**: Any Protocol implementation is swappable
- **Interface Segregation**: Minimal Protocol interfaces
- **Dependency Inversion**: Depend on Protocols, not concrete classes

### 4. Protocol-Based Design

```python
class Extractor(Protocol):
    def __call__(self, history: list, message: str) -> dict: ...

# Any implementation works
extract.node(state, NameExtractorDSPy(), "customer.first_name")
extract.node(state, NameExtractorRegex(), "customer.first_name")
```

## Troubleshooting

### Ollama Connection Issues

```bash
# Start Ollama server
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

### Brain Not Processing

Check environment variables:

```bash
# Ensure brain is enabled
BRAIN_ENABLED=true

# Check mode
BRAIN_MODE=shadow  # or reflex/conscious
```

### Celery Tasks Not Running

```bash
# Start Celery worker
celery -A src.tasks.celery_app worker --loglevel=info

# Check task status
celery -A src.tasks.celery_app inspect active
```

### Database Issues

```bash
# Recreate brain tables
python -c "from src.db.brain_migrations import create_brain_tables; create_brain_tables()"
```

## Documentation

- **Brain System**: `docs/BRAIN_SYSTEM_IMPLEMENTATION.md`
- **Quick Start**: `docs/BRAIN_QUICK_START.md`
- **Architecture**: `docs/V2_NODE_DESIGN_BLENDER_PRINCIPLES.md`
- **Atomic Nodes**: `docs/ATOMIC_NODES_THE_RIGHT_ABSTRACTION.md`
- **Testing**: `docs/TESTING_MULTI_CUSTOMER.md`

## Technology Stack

- **Framework**: FastAPI 0.110+
- **LLM Framework**: DSPy + LangGraph
- **Validation**: Pydantic 2.0+
- **Database**: SQLite (checkpoints + brain gym)
- **Background Tasks**: Celery
- **Testing**: pytest + pytest-asyncio
- **Type Checking**: mypy, ruff
- **Local LLM**: Ollama (llama3.2)

## Contributing

1. Follow file size limits (100 lines max)
2. Use Protocol-based design
3. Write tests for all features
4. Run `ruff check` before committing
5. Update documentation

## License

Proprietary - Yawlit Technologies

## Support

For issues or questions, contact the development team or file an issue in the project repository.

---

**Built with** LangGraph, DSPy, FastAPI, and Ollama
