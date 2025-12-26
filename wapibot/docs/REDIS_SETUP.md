# Redis Setup with Docker Desktop

## Prerequisites

- Docker Desktop installed and running
- Docker Compose V2

## Quick Start with Docker Desktop GUI

### 1. Open Docker Desktop
- Launch **Docker Desktop** from your applications
- Wait for it to fully start (Docker icon should be stable)

### 2. Start Redis Container

**Option A: Using Docker Desktop GUI (Recommended)**

1. Open **Docker Desktop** → Go to **Containers** tab
2. Look for the file icon 📁 → Click **"Open in VS Code"** or use terminal
3. In the directory where `docker-compose.yml` is located, open terminal:
   ```bash
   cd /home/riju279/Documents/Code/yawlit/wapibot/Wapi_bot/wapibot
   ```

4. Start Redis:
   ```bash
   docker compose up -d redis
   ```

5. In Docker Desktop, you'll see **wapibot-redis** container:
   - Green status = Running ✅
   - Can see logs by clicking the container
   - Can stop/restart from the UI

**Option B: Using Docker Desktop in Compose View (if available)**

1. Open Docker Desktop
2. Look for **Compose** section in left sidebar
3. You should see your compose file listed
4. Click the play ▶️ icon to start all services
5. Click the container name to view logs

### 3. Verify Redis is Running

**Via Docker Desktop:**
- Open the `wapibot-redis` container logs
- Look for: `Ready to accept connections`

**Via Command Line:**
```bash
docker compose ps
```

Expected output:
```
NAME                COMMAND                  SERVICE   STATUS
wapibot-redis       "redis-server --app..."  redis     Up (healthy)
```

**Test Connection:**
```bash
docker exec wapibot-redis redis-cli ping
```

Expected output:
```
PONG
```

### 4. Access Redis

**From Python code (Backend):**
```python
# Celery will connect to:
# redis://localhost:6379/0   (Broker)
# redis://localhost:6379/1   (Result backend)
```

**From Command Line (Interactive Redis CLI):**
```bash
docker exec -it wapibot-redis redis-cli
```

Then you can run Redis commands:
```
redis> PING
PONG
redis> INFO server
redis> DBSIZE
redis> KEYS *
redis> exit
```

## Docker Desktop Management

### View Logs
1. Docker Desktop → **Containers** tab
2. Click `wapibot-redis` container
3. Logs appear in the panel below

### Stop Redis
**GUI Method:**
1. Docker Desktop → Find `wapibot-redis`
2. Click the **Stop** button (⏹️)

**CLI Method:**
```bash
docker compose stop redis
```

### Restart Redis
**GUI Method:**
1. Docker Desktop → Click `wapibot-redis`
2. Click **Restart** button (🔄)

**CLI Method:**
```bash
docker compose restart redis
```

### Delete Container & Data
**GUI Method:**
1. Docker Desktop → Right-click `wapibot-redis`
2. Select **Delete** (removes container)
3. Volume (`redis_data`) persists (use Volumes tab to delete)

**CLI Method:**
```bash
# Stop and remove container
docker compose down

# Also remove volumes
docker compose down -v
```

## Troubleshooting

### Redis won't start
```bash
# Check logs
docker compose logs redis

# Common issues:
# - Port 6379 already in use
# - Docker daemon not running
```

### Connection refused (localhost:6379)
1. Verify container is running: `docker compose ps`
2. Check Docker Desktop status (should have green Docker icon)
3. Verify port mapping: Container should have `0.0.0.0:6379->6379/tcp`

### Reset Everything
```bash
# Stop and remove everything
docker compose down -v

# Clean rebuild
docker compose up -d redis

# Verify
docker compose ps
```

## Configuration

### Current Redis Config (docker-compose.yml)

| Setting | Value | Purpose |
|---------|-------|---------|
| Image | `redis:7-alpine` | Lightweight Redis version 7 |
| Port | `6379` | Default Redis port |
| Volume | `redis_data:/data` | Persistent data storage |
| Command | `--appendonly yes` | AOF persistence (survives restarts) |
| Health Check | Every 5s | Auto-detect if Redis is healthy |
| Restart | `unless-stopped` | Auto-restart on Docker restart |

### Modify Configuration

Edit `docker-compose.yml` and change:

```yaml
# Example: Change port to 6380
ports:
  - "6380:6379"
```

Then restart:
```bash
docker compose restart redis
```

## Backend Integration

The backend expects Redis at:
- **Broker**: `redis://localhost:6379/0`
- **Result Backend**: `redis://localhost:6379/1`

These are already configured in `.env.txt`:
```bash
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

## Running Celery Worker

Once Redis is running, start the Celery worker:

```bash
cd backend
celery -A tasks worker --loglevel=info
```

Celery will automatically connect to Redis and start processing payment reminder tasks.

## Docker Desktop Dashboard

### Useful Docker Desktop Features

1. **Real-time CPU/Memory Usage**: See container resource usage
2. **Stats Tab**: Performance metrics
3. **Inspect Tab**: View environment variables and configuration
4. **Logs Tab**: Streaming logs with filters
5. **Terminal**: Direct shell access to running container

## Health Check

The container includes a health check that:
- Runs every 5 seconds
- Sends `PING` to Redis
- Marks as "healthy" when responding
- Automatically restarts if unhealthy 3 times

View health status:
```bash
docker inspect wapibot-redis | grep -A 3 Health
```

---

**You're all set!** Redis is ready for your payment system. 🎉
