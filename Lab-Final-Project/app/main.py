import time
import json
import uuid
import logging
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, HTTPException, Request
from pydantic import BaseModel
import redis

from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget

# ---------------------------------------------------------
# Structured JSON Logging
# ---------------------------------------------------------
class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module
        }
        return json.dumps(log_record)

logger = logging.getLogger(__name__)
logger.setLevel(settings.LOG_LEVEL)
handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())
# Remove default handlers and add JSON handler
logging.root.handlers = [handler]

# ---------------------------------------------------------
# Redis Setup for Stateless Storage
# ---------------------------------------------------------
try:
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
    r.ping()
    REDIS_OK = True
    logger.info("Connected to Redis successfully.")
except Exception as e:
    logger.warning(f"Failed to connect to Redis: {e}")
    REDIS_OK = False
    r = None

# ---------------------------------------------------------
# Graceful Shutdown & Application State
# ---------------------------------------------------------
START_TIME = time.time()
_is_ready = False
_in_flight_requests = 0

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _is_ready
    logger.info("Initializing Agent API...")
    _is_ready = True
    logger.info("Agent is ready to accept requests.")
    
    yield
    
    _is_ready = False
    logger.info("Graceful shutdown initiated (SIGTERM received). Stop accepting new requests.")
    timeout = 30
    elapsed = 0
    while _in_flight_requests > 0 and elapsed < timeout:
        logger.info(f"Waiting for {_in_flight_requests} in-flight requests to complete...")
        time.sleep(1)
        elapsed += 1
    logger.info("Shutdown complete.")

app = FastAPI(title="Final Project AI Agent", lifespan=lifespan)

@app.middleware("http")
async def track_in_flight(request: Request, call_next):
    global _in_flight_requests
    _in_flight_requests += 1
    try:
        response = await call_next(request)
        return response
    finally:
        _in_flight_requests -= 1

# ---------------------------------------------------------
# Endpoints
# ---------------------------------------------------------

@app.get("/health")
def health():
    """Liveness probe: Checks if the agent process is still running."""
    return {
        "status": "ok",
        "uptime_seconds": round(time.time() - START_TIME, 1)
    }

@app.get("/ready")
def ready():
    """Readiness probe: Checks if dependencies (like Redis) are connected."""
    if not _is_ready:
        raise HTTPException(503, "Agent is starting up or shutting down.")
    
    if not REDIS_OK:
        raise HTTPException(503, "Redis is not connected.")
    try:
        r.ping()
    except Exception:
        raise HTTPException(503, "Redis ping failed.")
        
    return {"status": "ready"}

class ChatRequest(BaseModel):
    question: str
    session_id: str | None = None

def mock_llm_call(question: str, history: list) -> str:
    """Mock LLM API call."""
    time.sleep(0.5)  # Simulate LLM network latency
    turns = len([m for m in history if m["role"] == "user"])
    return f"This is an AI response to '{question}'. Total previous turns: {turns}"

@app.post("/ask")
def ask(
    body: ChatRequest,
    user_id: str = Depends(verify_api_key),
    _rate_limit: None = Depends(check_rate_limit),
    _budget: None = Depends(check_budget)
):
    """
    Core API Endpoint
    1. Get conversation history from Redis
    2. Call LLM
    3. Save to Redis
    4. Return response
    """
    if not _is_ready:
        raise HTTPException(503, "Agent not ready")

    session_id = body.session_id or str(uuid.uuid4())
    history = []
    
    # 1. Get conversation history from Redis (Stateless design)
    if REDIS_OK:
        data = r.get(f"session:{session_id}")
        if data:
            history = json.loads(data)

    # 2. Call LLM (using mock LLM for this lab)
    answer = mock_llm_call(body.question, history)

    # 3. Save to Redis
    history.append({"role": "user", "content": body.question})
    history.append({"role": "assistant", "content": answer})
    
    # Keep only last 20 messages (10 turns) to prevent context window overflow
    if len(history) > 20:
        history = history[-20:]

    if REDIS_OK:
        r.setex(f"session:{session_id}", 3600, json.dumps(history))

    # 4. Return response
    return {
        "session_id": session_id,
        "question": body.question,
        "answer": answer,
        "history_length": len(history)
    }