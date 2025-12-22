# Yawlit WhatsApp Bot - Simplified 24-Hour Implementation Plan

## PROBLEM STATEMENT

- **Pain Point 1:** "a LOT of challenge getting data reliably and keeping it"
- **Pain Point 2:** "state based race conditions in name, vehicle, date, address, service booking"
- **Constraint:** 24-hour deadline, must be stable and reliable
- **Scope:** 2 features (mass marketing + customer booking), not 11 planned features

## SOLUTION: DUAL-PERSISTENCE ARCHITECTURE

### Core Design Decisions

1. **SQLModel + Redis** (not Redis-only) = ACID transactions + distributed locks
2. **5 states, not 7** = IDLE → COLLECTING → CONFIRMING → COMPLETED, plus CANCELLED
3. **15 core modules, not 30+** = focused on reliability, not feature-rich
4. **Template responses, not LLM generation** = consistency over flexibility
5. **Single LLM extraction call** = fewer failure points, not 7 separate calls
6. **Merge-only updates** = never overwrite existing data

### Why This Works for Your Use Case

- **Prevents data loss:** SQLModel provides ACID transactions, database is source of truth
- **Prevents race conditions:** Redis distributed locks (5s timeout) prevent parallel processing
- **Prevents data overwrite:** merge() logic only sets non-null values
- **Prevents state-based bugs:** Clear state transitions, atomic operations
- **Achievable in 24h:** Simplified scope, proven patterns from example chatbot

---

## ARCHITECTURE OVERVIEW

### Layer 1: Database (SQLModel)

```
Conversation (conversation_id, state, created_at, updated_at)
  ├── Booking (all 16 fields, completeness, service_request_id)
  └── Message (role, content, timestamp) [for debugging/replay]
```

**Critical:** Single Booking record = single source of truth. No data loss.

### Layer 2: Concurrency (Redis)

- Distributed locks with 5s timeout
- Only one request processes per conversation_id at a time
- Prevents double-bookings, parallel state changes

### Layer 3: Processing (LLM + Validation)

- Single DSPy extraction signature for ALL fields at once
- Confidence threshold = 0.6 (reliable extraction)
- Fallback to regex for phone/date/plate
- No LLM-generated responses (only templates)

### Layer 4: Business Logic (State Machine)

- 5 states with clear transitions
- Completeness triggers confirmation at 75% (12/16 fields)
- Responses built from templates, not LLM
- No sentiment analysis, typo detection in v1

### Layer 5: Integrations (External APIs)

- Frappe: 5 APIs (services, addons, slots, pricing, create_booking)
- WAPI: Send message, send buttons, send template, webhook receive
- Retry policy: exponential backoff with 3 attempts

---

## MODULE BREAKDOWN (15 Core Modules)

### Database Layer (3 modules)

```
db/
├── models.py (50 lines) - SQLModel schemas
├── session.py (40 lines) - DB connection & management
└── repository.py (50 lines) - CRUD with atomic transactions
```

**Key:** `update_booking()` merges data without overwriting

### Concurrency Layer (2 modules)

```
core/locks/
├── redis_lock.py (45 lines) - Distributed locking
└── lock_decorator.py (30 lines) - @with_conversation_lock
```

**Key:** Context manager ensures lock release, prevents deadlocks

### Extraction Layer (3 modules)

```
core/extractors/
├── dspy_setup.py (40 lines) - Configure DSPy (Ollama/OpenRouter)
├── unified_extractor.py (50 lines) - Single LLM signature for all fields
└── regex_fallback.py (45 lines) - Phone, date, plate patterns
```

**Key:** LLM → confidence check → regex fallback → ask again

### Business Logic (4 modules)

```
core/
├── state_manager.py (50 lines) - State transitions
├── completeness.py (35 lines) - Calculate % (filled/16 fields)
├── response_builder.py (50 lines) - Template-based responses
└── validation.py (45 lines) - Field validators
```

**Key:** No decision-making complexity, just templates

### Integration Layer (3 modules)

```
integrations/
├── frappe_client.py (50 lines) - All Frappe APIs with retry
├── wapi_client.py (50 lines) - All WAPI endpoints
└── retry_policy.py (30 lines) - Tenacity configuration
```

**Key:** Retry on failures, timeouts = 5-10s

### Main Entry Point (1 module)

```
main.py (100 lines) - FastAPI + orchestration
```

**Endpoints:**

- `POST /webhook/chat` - Main conversation handler
- `POST /api/campaigns/send` - Mass marketing API

---

## DATABASE SCHEMA (SQLModel)

### Conversation

```
conversation_id: str (PRIMARY, indexed, = phone_number)
state: enum (IDLE|COLLECTING|CONFIRMING|COMPLETED|CANCELLED)
created_at, updated_at: datetime
```

### Booking (scratchpad)

```
CUSTOMER (4): first_name, last_name, phone, [address]
VEHICLE (3): vehicle_brand, vehicle_model, vehicle_plate
APPOINTMENT (4): appointment_date, service_type, time_slot, [address]
OPTIONAL (2): addons (JSON), notes
METADATA: service_request_id, completeness (0.0-100.0)
```

**Why 16 fields:** 12 required (for 75% trigger), 4 optional. Exact split matters.

### Message

```
conversation_id (FK), role (user|assistant), content, timestamp
```

**Why:** Debug/replay conversations if scratchpad corrupted.

---

## STATE MACHINE (5 States)

```
IDLE → COLLECTING → CONFIRMING → COMPLETED
       ↑                            ↑
       └────────── CANCELLED ───────┘
```

### Transitions

| Current | Trigger | Next | Action |
|---------|---------|------|--------|
| IDLE | Any message | COLLECTING | Start form |
| COLLECTING | completeness >= 75% | CONFIRMING | Show summary |
| CONFIRMING | User says "Confirm" | COMPLETED | Create booking in Frappe |
| CONFIRMING | User says "Edit X" | COLLECTING | Update field X |
| Any | User says "Cancel" | CANCELLED | Clear scratchpad, restart |

**Why 5 states:** No separate states for name/vehicle/date. All collected in COLLECTING state. LLM extracts all fields in parallel.

---

## CRITICAL FEATURES TO SOLVE YOUR PAIN POINTS

### Feature 1: Atomic Data Updates (Prevent Overwrite)

```python
# In repository.py
def update_booking(session, conv_id, extracted_data):
    booking = get_booking(session, conv_id)

    for field, value in extracted_data.items():
        if value is not None:  # ONLY set non-null values
            setattr(booking, field, value)

    booking.completeness = calculate_completeness(booking)
    session.commit()  # ACID transaction
```

**Problem solved:** Editing phone won't clear name.

### Feature 2: Distributed Locks (Prevent Race Conditions)

```python
# In main.py @handle_chat
@with_conversation_lock(timeout=5)  # Only one request at a time
def handle_chat(request: ChatRequest):
    with atomic_transaction(session):
        # ... all operations ...
```

**Problem solved:** Button click + text message at same time won't create duplicate bookings.

### Feature 3: Single LLM Extraction (Fewer Failure Points)

```python
# In unified_extractor.py
extract_result = extract_booking_data(
    message,        # User's message
    history         # Last 3 messages
)
# Returns: {first_name, last_name, phone, ..., intent, confidence}
```

**Problem solved:** Extracts ALL fields in one call, not 7 separate calls.

### Feature 4: Template-Based Responses (Consistent)

```python
TEMPLATES = {
    "collecting_need_name": "Hi! What's your name?",
    "collecting_need_phone": "Great! What's your phone number?",
    ...
}
```

**Problem solved:** No LLM hallucinations, consistent UX.

---

## MASS MARKETING API (Simple Pipeline)

```
Frappe UI → FastAPI /api/campaigns/send → WAPI Template Batch
```

### Implementation

```python
# integrations/mass_marketing.py
@app.post("/api/campaigns/send")
def send_marketing_campaign(campaign: CampaignRequest):
    for phone in campaign.recipients:
        send_template(phone, campaign.template_name, fields)
    return {"sent": count, "failed": count}
```

**Frappe Integration (via webhook/custom script):**

- Frappe button calls FastAPI endpoint
- FastAPI sends templates to all recipients via WAPI
- Returns count of sent/failed

---

## TESTING STRATEGY (4-6 Hours)

### Priority 1: Data Integrity (Hour 14-16)

- `test_no_data_overwrite()` - Update phone shouldn't clear name
- `test_atomic_transactions()` - Rollback on failure
- `test_completeness_calculation()` - 75% trigger works

### Priority 2: Concurrency (Hour 16-18)

- `test_no_double_booking()` - Thread 1: confirm, Thread 2: message
- `test_lock_timeout()` - Lock released after 5s
- `test_sequential_requests()` - Normal requests work with lock

### Priority 3: E2E Flow (Hour 18-20)

- `test_happy_path()` - Greeting → all fields → confirm → booking
- `test_edit_flow()` - Provide data → edit → confirm
- `test_cancel_flow()` - User cancels, can restart

### Tools

- `pytest` for unit tests
- `threading` for concurrency tests
- Mock Frappe/WAPI responses

---

## DOCKER SETUP

### docker-compose.yml

```yaml
services:
  wapibot:
    build: .
    ports: ["8000:8000"]
    env: DATABASE_URL, REDIS_HOST, OLLAMA_BASE_URL, WAPI_TOKEN
    depends_on: [postgres, redis]

  postgres:
    image: postgres:15-alpine
    ports: ["5433:5432"]  # NOT 5432 (Frappe might use it)
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:
    image: redis:7-alpine
    ports: ["6380:6379"]  # External: 6380, Internal: 6379
    volumes: [redis_data:/data]
```

### Dockerfile

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python -c "from db.session import init_db; init_db()"
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## DEVELOPMENT TIMELINE (24 Hours)

### Phase 1: Infrastructure (Hours 0-6)

- [0-1] Setup: venv, requirements, Docker skeleton
- [1-2] Models: SQLModel schemas, Pydantic validators
- [2-3] Database: session.py, repository.py
- [3-4] Locks: redis_lock.py, decorators
- [4-5] Extraction: dspy_setup.py, unified_extractor.py, regex_fallback.py
- [5-6] Response: response_builder.py, templates

### Phase 2: Integrations (Hours 6-10)

- [6-7] Frappe client: get_services, get_slots, calculate_price, create_booking
- [7-8] WAPI client: send_message, send_buttons, send_template
- [8-9] State manager: transitions, completeness
- [9-10] Main endpoint: /webhook/chat orchestration

### Phase 3: Testing (Hours 10-20)

- [10-12] Unit tests: database, locks, extractors
- [12-14] Integration tests: Frappe/WAPI mocks
- [14-16] E2E tests: happy path, concurrent requests
- [16-20] Run tests, fix failures, load testing

### Phase 4: Deployment (Hours 20-24)

- [20-21] Docker build, compose up locally
- [21-22] Environment setup, final config
- [22-23] Deploy to AWS/DO, smoke tests
- [23-24] Monitor, document

---

## CRITICAL FILES (Implement in This Order)

1. **db/models.py** - SQLModel schemas (foundation)
2. **db/repository.py** - Atomic update_booking() logic
3. **core/locks/redis_lock.py** - Distributed locking
4. **core/extractors/unified_extractor.py** - LLM extraction
5. **main.py** - Orchestrate everything

---

## KEY SIMPLIFICATIONS (vs Documented Plan)

| Feature | Documented | Simplified | Reason |
|---------|-----------|-----------|--------|
| States | 7 | 5 | Skip name/vehicle/date states |
| Modules | 30+ | 15 | Focus on core flows |
| LLM Extraction | 7 separate calls | 1 call | Fewer failure points |
| Responses | LLM generated | Templates | Consistent, no hallucinations |
| NLP | Sentiment, typo detect | None | Can add v2 |
| Locks | Complex state locks | Simple redis locks | Easier to debug |
| Database | Redis only | SQLModel + Redis | ACID safety |

---

## DEPLOYMENT TARGETS

### Local Testing

- PostgreSQL on localhost:5433
- Redis on localhost:6380
- Ollama on localhost:11434
- Frappe on <https://yawlit.duckdns.org>
- WAPI configured with credentials

### AWS/Digital Ocean

- Docker image pushed to registry
- RDS PostgreSQL or managed Postgres
- ElastiCache Redis or managed Redis
- FastAPI on EC2/App Platform
- Environment variables in .env

---

## SUCCESS CRITERIA (24-Hour Validation)

- ✅ Data doesn't overwrite on edits (unit test passes)
- ✅ No race conditions (concurrency tests pass)
- ✅ Happy path booking works (E2E test passes)
- ✅ Handles timeouts/retries gracefully
- ✅ Docker compose up works locally
- ✅ Deployed to cloud environment
- ✅ Manual WhatsApp testing works end-to-end
