#server/routers/chat_router.py
from fastapi import APIRouter, Request, HTTPException, Header
from web.services.chat_service import handle_chat
from web.services.magic_service import handle_magic
from web.services.stream_service import get_stream_task
from typing import Dict, Optional
import sqlite3
from pathlib import Path

router = APIRouter(prefix="/api")

import os
from web.services.config_service import DB_DIR
AUTH_DB = os.path.join(DB_DIR, "localmanus.db")

def validate_local_token(token: str) -> bool:
    if not token.startswith("local_"):
        return True
    conn = sqlite3.connect(AUTH_DB, timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM auth_tokens WHERE token = ? AND expires_at > ?", (token, __import__("time").time()))
    result = cur.fetchone()
    conn.close()
    return result is not None

@router.post("/chat")
async def chat(request: Request, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization[7:]
    if token.startswith("local_") and not validate_local_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    data = await request.json()
    await handle_chat(data)
    return {"status": "done"}

@router.post("/cancel/{session_id}")
async def cancel_chat(session_id: str):
    """
    Endpoint to cancel an ongoing stream task for a given session_id.

    If the task exists and is not yet completed, it will be cancelled.

    Path parameter:
        session_id (str): The ID of the session whose task should be cancelled.

    Response:
        {"status": "cancelled"} if the task was cancelled.
        {"status": "not_found_or_done"} if no such task exists or it is already done.
    """
    task = get_stream_task(session_id)
    if task and not task.done():
        task.cancel()
        return {"status": "cancelled"}
    return {"status": "not_found_or_done"}

@router.post("/magic")
async def magic(request: Request, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization[7:]
    if token.startswith("local_") and not validate_local_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    data = await request.json()
    await handle_magic(data)
    return {"status": "done"}

@router.post("/magic/cancel/{session_id}")
async def cancel_magic(session_id: str) -> Dict[str, str]:
    """
    Endpoint to cancel an ongoing magic generation task for a given session_id.

    If the task exists and is not yet completed, it will be cancelled.

    Path parameter:
        session_id (str): The ID of the session whose task should be cancelled.

    Response:
        {"status": "cancelled"} if the task was cancelled.
        {"status": "not_found_or_done"} if no such task exists or it is already done.
    """
    task = get_stream_task(session_id)
    if task and not task.done():
        task.cancel()
        return {"status": "cancelled"}
    return {"status": "not_found_or_done"}
