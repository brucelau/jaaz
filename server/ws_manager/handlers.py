from .manager import sio, add_connection, remove_connection
from services.log_service import ws_logger as logger


@sio.event
async def connect(sid, environ, auth):
    logger.info("ws_client_connect", sid=sid)
    user_info = auth or {}
    add_connection(sid, user_info)
    await sio.emit('connected', {'status': 'connected'}, room=sid)


@sio.event
async def disconnect(sid):
    logger.info("ws_client_disconnect", sid=sid)
    remove_connection(sid)


@sio.event
async def ping(sid, data):
    await sio.emit('pong', data, room=sid)
