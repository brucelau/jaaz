from fastapi import APIRouter, Request, HTTPException, Header
from services.chat_service import handle_chat
from db.db_service import db_service
import asyncio
import json
from pathlib import Path
import sqlite3
from typing import Optional

router = APIRouter(prefix="/api/canvas")

AUTH_DB = Path(__file__).parent.parent / "auth.db"

def validate_local_token(token: str) -> bool:
    if not token.startswith("local_"):
        return True
    conn = sqlite3.connect(AUTH_DB, timeout=10)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM tokens WHERE token = ? AND expires_at > ?", (token, __import__("time").time()))
    result = cur.fetchone()
    conn.close()
    return result is not None

@router.get("/list")
async def list_canvases():
    return await db_service.list_canvases()

@router.post("/create")
async def create_canvas(request: Request, authorization: Optional[str] = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authentication required")
    token = authorization[7:]
    if token.startswith("local_") and not validate_local_token(token):
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    data = await request.json()
    id = data.get('canvas_id')
    name = data.get('name')

    asyncio.create_task(handle_chat(data))
    await db_service.create_canvas(id, name)
    return {"id": id }

@router.get("/{id}")
async def get_canvas(id: str):
    return await db_service.get_canvas_data(id)

@router.post("/{id}/save")
async def save_canvas(id: str, request: Request):
    payload = await request.json()
    data_str = json.dumps(payload['data'])
    await db_service.save_canvas_data(id, data_str, payload['thumbnail'])
    return {"id": id }

@router.post("/{id}/rename")
async def rename_canvas(id: str, request: Request):
    data = await request.json()
    name = data.get('name')
    await db_service.rename_canvas(id, name)
    return {"id": id }

@router.delete("/{id}/delete")
async def delete_canvas(id: str):
    await db_service.delete_canvas(id)
    return {"id": id }