from .manager import sio, add_connection, remove_connection, active_connections
from web.services.log_service import ws_logger as logger
import sqlite3
from pathlib import Path

import os
from web.services.config_service import DB_DIR
AUTH_DB = os.path.join(DB_DIR, "localmanus.db")
MANUS_DB = AUTH_DB


def validate_local_token(token: str) -> bool:
    if not token.startswith("local_"):
        return True
    conn = sqlite3.connect(AUTH_DB, timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM auth_tokens WHERE token = ? AND expires_at > ?", (token, __import__("time").time()))
    result = cur.fetchone()
    conn.close()
    return result is not None


def session_exists(session_id: str) -> bool:
    conn = sqlite3.connect(MANUS_DB, timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM chat_sessions WHERE id = ?", (session_id,))
    result = cur.fetchone()
    conn.close()
    return result is not None


@sio.event
async def connect(sid, environ, auth):
    token = auth.get("token") if auth else None
    authenticated = True
    if token and token.startswith("local_") and not validate_local_token(token):
        logger.warning("ws_client_rejected", sid=sid, reason="invalid_token")
        authenticated = False
    logger.info("ws_client_connect", sid=sid)
    user_info = auth or {}
    add_connection(sid, user_info, authenticated)
    await sio.emit('connected', {'status': 'connected'}, room=sid)


@sio.event
async def join_session(sid, data):
    conn_info = active_connections.get(sid, {})
    if not conn_info.get('authenticated', False):
        logger.warning("join_session_rejected", sid=sid, reason="not_authenticated")
        await sio.emit('error', {'message': 'Authentication required'}, room=sid)
        return
    session_id = data.get('session_id') if isinstance(data, dict) else data
    if session_id and session_exists(session_id):
        await sio.enter_room(sid, room=session_id)
        logger.info("session_room_joined", session_id=session_id, sid=sid)
    else:
        logger.warning("join_session_rejected", sid=sid, session_id=session_id, reason="session_not_found")
        await sio.emit('error', {'message': 'Session not found'}, room=sid)


@sio.event
async def disconnect(sid):
    logger.info("ws_client_disconnect", sid=sid)
    remove_connection(sid)


@sio.event
async def ping(sid, data):
    await sio.emit('pong', data, room=sid)
