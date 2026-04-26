from services.websocket_state import sio, get_all_socket_ids
import traceback
from typing import Any, Dict
from services.log_service import ws_logger as logger


async def broadcast_session_update(session_id: str, canvas_id: str | None, event: Dict[str, Any]):
    socket_ids = get_all_socket_ids()
    if socket_ids:
        try:
            for socket_id in socket_ids:
                await sio.emit('session_update', {
                    'canvas_id': canvas_id,
                    'session_id': session_id,
                    **event
                }, room=socket_id)
        except Exception as e:
            logger.error("broadcast_session_update_failed", session_id=session_id, error=str(e))


async def send_to_websocket(session_id: str, event: Dict[str, Any]):
    await broadcast_session_update(session_id, None, event)


async def broadcast_init_done():
    try:
        await sio.emit('init_done', {
            'type': 'init_done'
        })
        logger.info("init_done_broadcasted")
    except Exception as e:
        logger.error("init_done_broadcast_failed", error=str(e))
