"""
OmniMind AI — Redis Event Bus for Agent Log Streaming

When Redis is unavailable, falls back to an in-process asyncio queue
so development and tests work without Redis installed.
"""
import json
import logging
import asyncio
from typing import AsyncGenerator, Optional

logger = logging.getLogger("omnimind.backend.events")

# ── In-process fallback queue (when Redis is unavailable) ────────────────────
_in_memory_queues: dict[str, asyncio.Queue] = {}


def _get_or_create_queue(channel: str) -> asyncio.Queue:
    if channel not in _in_memory_queues:
        _in_memory_queues[channel] = asyncio.Queue(maxsize=1000)
    return _in_memory_queues[channel]


# ── Redis client (optional) ───────────────────────────────────────────────────
_redis_client = None
_redis_available = False


def _try_init_redis():
    """Attempt to connect to Redis. Silently falls back if unavailable."""
    global _redis_client, _redis_available
    try:
        import redis
        from config import settings
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=1)
        _redis_client.ping()
        _redis_available = True
        logger.info("Redis event bus connected successfully.")
    except Exception as e:
        logger.warning(f"Redis not available ({e}). Using in-process event queue fallback.")
        _redis_available = False


_try_init_redis()


def workflow_channel(workflow_id: str) -> str:
    """Return the Redis channel name for a workflow."""
    return f"omnimind:workflow:{workflow_id}:logs"


# ── Publish (called from Celery tasks / agents) ───────────────────────────────

def publish_agent_event(
    workflow_id: str,
    agent_name: str,
    log_type: str,
    content: str,
    task_id: Optional[str] = None,
):
    """Publish an agent log event to Redis or in-process queue."""
    event = {
        "workflow_id": workflow_id,
        "task_id": task_id,
        "agent_name": agent_name,
        "log_type": log_type,
        "content": content,
    }
    channel = workflow_channel(workflow_id)
    payload = json.dumps(event)

    if _redis_available and _redis_client:
        try:
            _redis_client.publish(channel, payload)
            return
        except Exception as e:
            logger.warning(f"Redis publish failed ({e}). Falling back to in-process queue.")

    # In-process fallback — put_nowait avoids blocking in sync context
    q = _get_or_create_queue(channel)
    try:
        q.put_nowait(payload)
    except asyncio.QueueFull:
        pass  # Drop oldest if queue full


# ── Subscribe (called from WebSocket handler) ──────────────────────────────────

async def subscribe_workflow_events(
    workflow_id: str,
    timeout_seconds: float = 300.0,
) -> AsyncGenerator[dict, None]:
    """
    Async generator that yields agent log events for a workflow.
    Supports both Redis pub/sub and in-process asyncio queue fallback.
    """
    channel = workflow_channel(workflow_id)

    if _redis_available and _redis_client:
        yield {"log_type": "system", "content": "Connected to Redis event stream.", "agent_name": "System"}
        # Use redis-py's async pubsub
        try:
            import redis.asyncio as aioredis
            from config import settings
            async_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
            pubsub = async_client.pubsub()
            await pubsub.subscribe(channel)
            deadline = asyncio.get_event_loop().time() + timeout_seconds
            async for message in pubsub.listen():
                if asyncio.get_event_loop().time() > deadline:
                    break
                if message["type"] == "message":
                    try:
                        yield json.loads(message["data"])
                    except json.JSONDecodeError:
                        pass
                # Yield control periodically
                await asyncio.sleep(0)
            await pubsub.unsubscribe(channel)
            await async_client.aclose()
            return
        except Exception as e:
            logger.warning(f"Redis async subscribe failed ({e}). Falling back to in-process queue.")

    # In-process fallback
    yield {"log_type": "system", "content": "Connected to in-process event stream.", "agent_name": "System"}
    q = _get_or_create_queue(channel)
    deadline = asyncio.get_event_loop().time() + timeout_seconds

    while asyncio.get_event_loop().time() < deadline:
        try:
            payload = await asyncio.wait_for(q.get(), timeout=1.0)
            yield json.loads(payload)
        except asyncio.TimeoutError:
            # Send keepalive ping
            yield {"log_type": "ping", "content": "", "agent_name": "System"}
        except json.JSONDecodeError:
            pass


def publish_workflow_complete(workflow_id: str, success: bool, summary: str = ""):
    """Publish a terminal workflow-complete event."""
    publish_agent_event(
        workflow_id=workflow_id,
        agent_name="System",
        log_type="workflow_complete" if success else "workflow_failed",
        content=summary or ("Workflow completed successfully." if success else "Workflow failed."),
    )
