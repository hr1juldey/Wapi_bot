# Brain System - Quick Start Guide

**5-Minute Setup Guide**

---

## Prerequisites

- Backend server running
- Ollama installed (for dreaming)
- Celery worker running (optional, for scheduled tasks)

---

## Quick Setup

### 1. Enable Brain (Shadow Mode - Safe for Production)

Add to `.env.txt`:

```bash
# Enable brain in shadow mode (observe only, never act)
BRAIN_ENABLED=true
BRAIN_MODE=shadow

# Enable RL Gym logging
RL_GYM_ENABLED=true
RL_GYM_DB_PATH=brain_gym.db
```

### 2. Initialize Database

```bash
cd backend
python3 -c "from src.db.brain_migrations import create_brain_tables; create_brain_tables('brain_gym.db')"
```

### 3. Restart Server

```bash
uvicorn src.main:app --reload --port 8000
```

### 4. Verify Brain is Running

Send a test message and check logs:

```bash
tail -f logs/app.log | grep "🧠"
```

Expected output:
```
🧠 Running brain in shadow mode
🧠 Brain processing complete
```

### 5. Check Brain Status

```bash
curl http://localhost:8000/brain/status
```

Expected response:
```json
{
  "enabled": true,
  "mode": "shadow",
  "features": {...},
  "metrics": {
    "dream_enabled": true,
    "rl_gym_enabled": true
  }
}
```

---

## View Logged Decisions

```bash
curl http://localhost:8000/brain/decisions?limit=10
```

---

## Enable Dreaming (Optional)

### 1. Install Ollama

```bash
curl https://ollama.ai/install.sh | sh
ollama serve
```

### 2. Pull Model

```bash
ollama pull llama3.2
```

### 3. Enable Dreaming

Add to `.env.txt`:

```bash
DREAM_ENABLED=true
DREAM_OLLAMA_MODEL=llama3.2
DREAM_MIN_CONVERSATIONS=50
```

### 4. Start Celery Worker

```bash
celery -A src.tasks worker --loglevel=info
```

### 5. Trigger Dream Manually

```bash
curl -X POST http://localhost:8000/brain/dream \
  -H "Content-Type: application/json" \
  -d '{"force": true, "min_conversations": 30}'
```

---

## Upgrade to Conscious Mode (Advanced)

⚠️ **Warning:** Test thoroughly before production

### 1. Update .env.txt

```bash
# Switch to conscious mode
BRAIN_MODE=conscious

# Enable ONLY template customization first
BRAIN_ACTION_TEMPLATE_CUSTOMIZE=true

# Keep others disabled initially
BRAIN_ACTION_DATE_CONFIRM=false
BRAIN_ACTION_ADDON_SUGGEST=false
BRAIN_ACTION_QA_ANSWER=false
BRAIN_ACTION_BARGAINING_HANDLE=false
BRAIN_ACTION_ESCALATE_HUMAN=false
```

### 2. Restart and Monitor

```bash
uvicorn src.main:app --reload
tail -f logs/app.log | grep "🧠"
```

### 3. Gradually Enable Features

Test each toggle individually:

```bash
# Enable date confirmation
BRAIN_ACTION_DATE_CONFIRM=true

# Test with conversations involving dates
# Monitor RL Gym decisions
curl http://localhost:8000/brain/decisions?limit=20
```

---

## Common Commands

```bash
# Check brain status
curl http://localhost:8000/brain/status

# Get recent decisions
curl http://localhost:8000/brain/decisions?limit=50

# Get feature toggles
curl http://localhost:8000/brain/features

# Trigger dream
curl -X POST http://localhost:8000/brain/dream -d '{"force": true}'

# Trigger GEPA training
curl -X POST http://localhost:8000/brain/train -d '{"num_iterations": 100}'
```

---

## Monitoring

### Check Brain Logs

```bash
# Real-time brain processing
tail -f logs/app.log | grep "🧠"

# Decision logging
tail -f logs/app.log | grep "Decision logged"

# Conflicts detected
tail -f logs/app.log | grep "Conflict detected"
```

### Query RL Gym Database

```bash
sqlite3 brain_gym.db "SELECT COUNT(*) FROM brain_decisions;"
sqlite3 brain_gym.db "SELECT conflict_detected, COUNT(*) FROM brain_decisions GROUP BY conflict_detected;"
```

---

## Troubleshooting

### Brain Not Appearing in Logs

```bash
# Check if enabled
grep BRAIN_ENABLED .env.txt

# Should show: BRAIN_ENABLED=true
```

### No Decisions in Database

```bash
# Check if RL Gym enabled
grep RL_GYM_ENABLED .env.txt

# Verify database exists
ls -lh brain_gym.db

# Check table structure
sqlite3 brain_gym.db ".schema brain_decisions"
```

### Dreaming Fails

```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Check model is available
ollama list | grep llama3.2

# View Celery logs
celery -A src.tasks worker --loglevel=debug
```

---

## Production Checklist

- [ ] Brain enabled in shadow mode
- [ ] RL Gym database created
- [ ] Server logs show brain processing
- [ ] Decisions being logged
- [ ] No errors in logs
- [ ] Latency acceptable (<500ms added)
- [ ] Memory usage acceptable
- [ ] Database growing as expected

---

## Next Steps

1. **Week 1:** Run in shadow mode, collect 500+ decisions
2. **Week 2:** Analyze RL Gym data, identify patterns
3. **Week 3:** Enable template customization in conscious mode
4. **Week 4:** Gradually enable other features
5. **Month 2:** Enable dreaming, start GEPA optimization

---

## Support

- Full documentation: `docs/BRAIN_SYSTEM_IMPLEMENTATION.md`
- Architecture plan: `docs/BIG_BRAIN.md`
- API endpoints: `http://localhost:8000/docs` (Swagger UI)

---

**Status:** Ready for Production (Shadow Mode)
**Recommended:** Start with shadow mode for 1-2 weeks before enabling conscious mode
