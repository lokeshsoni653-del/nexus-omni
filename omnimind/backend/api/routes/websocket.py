"""
OmniMind AI — WebSocket Agent Log Streaming Endpoint

Endpoint:
  - WS /ws/stream/{workflow_id} : Streams agent thoughts, actions, and results in real time.
"""
import json
import logging
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from omnimind.backend.events import subscribe_workflow_events

logger = logging.getLogger("omnimind.backend.api.routes.websocket")

router = APIRouter(prefix="/ws", tags=["WebSockets"])


@router.websocket("/stream/{workflow_id}")
async def websocket_agent_stream(
    websocket: WebSocket,
    workflow_id: str,
):
    """
    WebSocket endpoint for real-time agent thought streaming.

    Clients connect to /ws/stream/{workflow_id} to receive JSON events:
    {
        "workflow_id": "...",
        "agent_name": "Orchestrator",
        "log_type": "thought" | "action" | "result" | "error" | "workflow_complete",
        "content": "..."
    }
    """
    await websocket.accept()
    logger.info(f"WebSocket client connected for workflow stream: {workflow_id}")

    try:
        # Subscribe to Redis / in-process event channel
        async for event in subscribe_workflow_events(workflow_id, timeout_seconds=600):
            await websocket.send_json(event)
            
            # Close WebSocket gracefully when workflow reaches terminal event
            if event.get("log_type") in ("workflow_complete", "workflow_failed"):
                logger.info(f"Stream terminal event received for workflow {workflow_id}. Closing WS connection.")
                await websocket.send_json({
                    "log_type": "system",
                    "content": "Stream closed — workflow execution finished.",
                    "agent_name": "System",
                })
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket client disconnected from workflow stream: {workflow_id}")
    except Exception as exc:
        logger.error(f"WebSocket error on stream {workflow_id}: {exc}")
        try:
            await websocket.send_json({
                "log_type": "error",
                "content": f"WebSocket error: {str(exc)}",
                "agent_name": "System",
            })
            await websocket.close()
        except Exception:
            pass
