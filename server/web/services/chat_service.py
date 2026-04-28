import asyncio
import json
from typing import Dict, Any, List, Optional
from models.tool_model import ToolInfoJson
from database.db_service import db_service
from agents.langgraph_service import langgraph_multi_agent
from web.websocket.emitter import send_to_websocket
from web.services.stream_service import add_stream_task, remove_stream_task
from models.config_model import ModelInfo
from web.services.log_service import chat_logger as logger


async def handle_chat(data: Dict[str, Any]) -> None:
    """
    Handle an incoming chat request.

    Workflow:
    - Parse incoming chat data.
    - Optionally inject system prompt.
    - Save chat session and messages to the database.
    - Launch langgraph_agent task to process chat.
    - Manage stream task lifecycle (add, remove).
    - Notify frontend via WebSocket when stream is done.

    Args:
        data (dict): Chat request data containing:
            - messages: list of message dicts
            - session_id: unique session identifier
            - canvas_id: canvas identifier (contextual use)
            - text_model: text model configuration
            - tool_list: list of tool model configurations (images/videos)
    """
    # Extract fields from incoming data
    messages: List[Dict[str, Any]] = data.get('messages', [])
    session_id: str = data.get('session_id', '')
    canvas_id: str = data.get('canvas_id', '')
    text_model: ModelInfo = data.get('text_model', {})
    tool_list: List[ToolInfoJson] = data.get('tool_list', [])

    logger.debug("chat_service_received", tool_list=tool_list)

    # TODO: save and fetch system prompt from db or settings config
    system_prompt: Optional[str] = data.get('system_prompt')

    if len(messages) == 1:
        prompt = messages[0].get('content', '')
        await db_service.create_chat_session_and_message(
            session_id,
            text_model.get('model'),
            text_model.get('provider'),
            canvas_id,
            messages[-1].get('role', 'user'),
            json.dumps(messages[-1]),
            prompt[:200] if isinstance(prompt, str) else ''
        )
    elif len(messages) > 0:
        await db_service.create_message(session_id, messages[-1].get('role', 'user'), json.dumps(messages[-1]))

    # Create and start langgraph_agent task for chat processing
    task = asyncio.create_task(langgraph_multi_agent(
        messages, canvas_id, session_id, text_model, tool_list, system_prompt))

    # Register the task in stream_tasks (for possible cancellation)
    add_stream_task(session_id, task)
    try:
        # Await completion of the langgraph_agent task
        await task
    except asyncio.exceptions.CancelledError:
        logger.warning("session_cancelled", session_id=session_id)
    finally:
        # Always remove the task from stream_tasks after completion/cancellation
        remove_stream_task(session_id)
        # Notify frontend WebSocket that chat processing is done
        await send_to_websocket(session_id, {
            'type': 'done'
        })
