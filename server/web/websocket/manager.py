import socketio
from typing import Dict
from web.services.log_service import ws_logger as logger

sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins='*',
    allow_upgrades=True,
    always_reject=False
)

active_connections: Dict[str, dict] = {}


def add_connection(socket_id: str, user_info: dict = None, authenticated: bool = True):
    active_connections[socket_id] = {'user_info': user_info or {}, 'authenticated': authenticated}
    logger.info("ws_connection_added", socket_id=socket_id, total=len(active_connections))


def remove_connection(socket_id: str):
    if socket_id in active_connections:
        del active_connections[socket_id]
        logger.info("ws_connection_removed", socket_id=socket_id, total=len(active_connections))


def get_all_socket_ids():
    return list(active_connections.keys())


def get_connection_count():
    return len(active_connections)
