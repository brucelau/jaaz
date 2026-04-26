import sqlite3
import json
import os
import asyncio
from typing import List, Dict, Any, Optional
import aiosqlite
from services.config_service import CONFIG_DIR
from .migrations.manager import MigrationManager, CURRENT_VERSION
from services.log_service import db_logger as logger

DB_PATH = os.path.join(CONFIG_DIR, "localmanus.db")


class ConnectionPool:
    """Lightweight connection pool for aiosqlite using persistent connections."""

    def __init__(self, database: str, min_connections: int = 1, max_connections: int = 10):
        self.database = database
        self.min_connections = min_connections
        self.max_connections = max_connections
        self._pool: List[aiosqlite.Connection] = []
        self._lock = asyncio.Lock()
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
        async with self._lock:
            if not self._initialized:
                for _ in range(self.min_connections):
                    conn = await aiosqlite.connect(self.database)
                    conn.row_factory = sqlite3.Row
                    self._pool.append(conn)
                self._initialized = True

    async def acquire(self) -> aiosqlite.Connection:
        await self.initialize()
        if self._pool:
            return self._pool.pop()
        return await aiosqlite.connect(self.database)

    async def release(self, conn: aiosqlite.Connection):
        try:
            if len(self._pool) < self.max_connections:
                self._pool.append(conn)
            else:
                await conn.close()
        except Exception:
            await conn.close()

    async def close_all(self):
        for conn in self._pool:
            await conn.close()
        self._pool.clear()
        self._initialized = False

    async def exec(self, query: str, params: tuple = ()) -> aiosqlite.Cursor:
        conn = await self.acquire()
        try:
            cursor = await conn.execute(query, params)
            return cursor, conn
        except Exception:
            await conn.close()
            raise

    async def commit_and_release(self, conn: aiosqlite.Connection):
        try:
            await conn.commit()
        finally:
            await self.release(conn)

    async def close(self):
        await self.close_all()


_db_pool: Optional[ConnectionPool] = None


async def get_db_pool() -> ConnectionPool:
    global _db_pool
    if _db_pool is None:
        _db_pool = ConnectionPool(DB_PATH, min_connections=1, max_connections=5)
        await _db_pool.initialize()
    return _db_pool


class DatabaseService:
    def __init__(self):
        self.db_path = DB_PATH
        self._ensure_db_directory()
        self._migration_manager = MigrationManager()
        self._init_db()

    def _ensure_db_directory(self):
        """Ensure the database directory exists"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

    def _init_db(self):
        """Initialize the database with the current schema"""
        with sqlite3.connect(self.db_path) as conn:
            # Create version table if it doesn't exist
            conn.execute("""
                CREATE TABLE IF NOT EXISTS db_version (
                    version INTEGER PRIMARY KEY
                )
            """)
            
            # Get current version
            cursor = conn.execute("SELECT version FROM db_version")
            current_version = cursor.fetchone()
            logger.info("db_version_check", current=current_version, latest=CURRENT_VERSION)
            
            if current_version is None:
                # First time setup - start from version 0
                conn.execute("INSERT INTO db_version (version) VALUES (0)")
                self._migration_manager.migrate(conn, 0, CURRENT_VERSION)
            elif current_version[0] < CURRENT_VERSION:
                logger.info("db_migrating", from_version=current_version[0], to_version=CURRENT_VERSION)
                # Need to migrate
                self._migration_manager.migrate(conn, current_version[0], CURRENT_VERSION)

    async def create_canvas(self, id: str, name: str):
        pool = await get_db_pool()
        cursor, conn = await pool.exec("""
            INSERT INTO canvases (id, name)
            VALUES (?, ?)
        """, (id, name))
        await pool.commit_and_release(conn)

    async def list_canvases(self) -> List[Dict[str, Any]]:
        pool = await get_db_pool()
        conn = await pool.acquire()
        try:
            conn.row_factory = sqlite3.Row
            cursor = await conn.execute("""
                SELECT id, name, description, thumbnail, created_at, updated_at
                FROM canvases
                ORDER BY updated_at DESC
            """)
            rows = await cursor.fetchall()
            result = [dict(row) for row in rows]
        finally:
            await pool.release(conn)
        return result

    async def create_chat_session(self, id: str, model: str, provider: str, canvas_id: str, title: Optional[str] = None):
        pool = await get_db_pool()
        cursor, conn = await pool.exec("""
            INSERT INTO chat_sessions (id, model, provider, canvas_id, title)
            VALUES (?, ?, ?, ?, ?)
        """, (id, model, provider, canvas_id, title))
        await pool.commit_and_release(conn)

    async def create_message(self, session_id: str, role: str, message: str):
        pool = await get_db_pool()
        cursor, conn = await pool.exec("""
            INSERT INTO chat_messages (session_id, role, message)
            VALUES (?, ?, ?)
        """, (session_id, role, message))
        await pool.commit_and_release(conn)

    async def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        pool = await get_db_pool()
        conn = await pool.acquire()
        try:
            conn.row_factory = sqlite3.Row
            cursor = await conn.execute("""
                SELECT role, message, id
                FROM chat_messages
                WHERE session_id = ?
                ORDER BY id ASC
            """, (session_id,))
            rows = await cursor.fetchall()
            messages = []
            for row in rows:
                row_dict = dict(row)
                if row_dict['message']:
                    try:
                        msg = json.loads(row_dict['message'])
                        messages.append(msg)
                    except:
                        pass
            return messages
        finally:
            await pool.release(conn)

    async def list_sessions(self, canvas_id: str) -> List[Dict[str, Any]]:
        pool = await get_db_pool()
        conn = await pool.acquire()
        try:
            conn.row_factory = sqlite3.Row
            if canvas_id:
                cursor = await conn.execute("""
                    SELECT id, title, model, provider, created_at, updated_at
                    FROM chat_sessions
                    WHERE canvas_id = ?
                    ORDER BY updated_at DESC
                """, (canvas_id,))
            else:
                cursor = await conn.execute("""
                    SELECT id, title, model, provider, created_at, updated_at
                    FROM chat_sessions
                    ORDER BY updated_at DESC
                """)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await pool.release(conn)

    async def save_canvas_data(self, id: str, data: str, thumbnail: str = None):
        pool = await get_db_pool()
        cursor, conn = await pool.exec("""
            UPDATE canvases
            SET data = ?, thumbnail = ?, updated_at = STRFTIME('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE id = ?
        """, (data, thumbnail, id))
        await pool.commit_and_release(conn)

    async def get_canvas_data(self, id: str) -> Optional[Dict[str, Any]]:
        pool = await get_db_pool()
        conn = await pool.acquire()
        try:
            conn.row_factory = sqlite3.Row
            cursor = await conn.execute("""
                SELECT data, name
                FROM canvases
                WHERE id = ?
            """, (id,))
            row = await cursor.fetchone()
            sessions = await self.list_sessions(id)
            if row:
                return {
                    'data': json.loads(row['data']) if row['data'] else {},
                    'name': row['name'],
                    'sessions': sessions
                }
            return None
        finally:
            await pool.release(conn)

    async def delete_canvas(self, id: str):
        pool = await get_db_pool()
        cursor, conn = await pool.exec("DELETE FROM canvases WHERE id = ?", (id,))
        await pool.commit_and_release(conn)

    async def rename_canvas(self, id: str, name: str):
        pool = await get_db_pool()
        cursor, conn = await pool.exec("UPDATE canvases SET name = ? WHERE id = ?", (name, id))
        await pool.commit_and_release(conn)

    async def create_comfy_workflow(self, name: str, api_json: str, description: str, inputs: str, outputs: str = None):
        pool = await get_db_pool()
        cursor, conn = await pool.exec("""
            INSERT INTO comfy_workflows (name, api_json, description, inputs, outputs)
            VALUES (?, ?, ?, ?, ?)
        """, (name, api_json, description, inputs, outputs))
        await pool.commit_and_release(conn)

    async def list_comfy_workflows(self) -> List[Dict[str, Any]]:
        pool = await get_db_pool()
        conn = await pool.acquire()
        try:
            conn.row_factory = sqlite3.Row
            cursor = await conn.execute("SELECT id, name, description, api_json, inputs, outputs FROM comfy_workflows ORDER BY id DESC")
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            await pool.release(conn)

    async def delete_comfy_workflow(self, id: int):
        pool = await get_db_pool()
        cursor, conn = await pool.exec("DELETE FROM comfy_workflows WHERE id = ?", (id,))
        await pool.commit_and_release(conn)

    async def get_comfy_workflow(self, id: int):
        pool = await get_db_pool()
        conn = await pool.acquire()
        try:
            conn.row_factory = sqlite3.Row
            cursor = await conn.execute(
                "SELECT api_json FROM comfy_workflows WHERE id = ?", (id,)
            )
            row = await cursor.fetchone()
            workflow_json = (
                row["api_json"]
                if isinstance(row["api_json"], dict)
                else json.loads(row["api_json"])
            )
            return workflow_json
        finally:
            await pool.release(conn)

# Create a singleton instance
db_service = DatabaseService()
