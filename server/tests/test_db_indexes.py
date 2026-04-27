import pytest
import os
import tempfile
import asyncio
from database.db_service import DatabaseService


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    yield path
    if os.path.exists(path):
        os.unlink(path)


class TestDatabaseIndexes:
    @pytest.mark.asyncio
    async def test_chat_sessions_canvas_id_index_exists(self, temp_db):
        import database.db_service as db_mod
        old_path = db_mod.DB_PATH
        old_pool = db_mod._db_pool
        db_mod.DB_PATH = temp_db
        db_mod._db_pool = None
        try:
            DatabaseService()
            pool = await db_mod.get_db_pool()
            conn = await pool.acquire()
            try:
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_chat_sessions_canvas'"
                )
                row = await cursor.fetchone()
                assert row is not None, "Index idx_chat_sessions_canvas does not exist"
            finally:
                await pool.release(conn)
        finally:
            db_mod.DB_PATH = old_path
            if db_mod._db_pool:
                await db_mod._db_pool.close_all()
            db_mod._db_pool = old_pool

    @pytest.mark.asyncio
    async def test_chat_messages_session_id_index_exists(self, temp_db):
        import database.db_service as db_mod
        old_path = db_mod.DB_PATH
        old_pool = db_mod._db_pool
        db_mod.DB_PATH = temp_db
        db_mod._db_pool = None
        try:
            DatabaseService()
            pool = await db_mod.get_db_pool()
            conn = await pool.acquire()
            try:
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_chat_messages_session'"
                )
                row = await cursor.fetchone()
                assert row is not None, "Index idx_chat_messages_session does not exist"
            finally:
                await pool.release(conn)
        finally:
            db_mod.DB_PATH = old_path
            if db_mod._db_pool:
                await db_mod._db_pool.close_all()
            db_mod._db_pool = old_pool

    @pytest.mark.asyncio
    async def test_canvases_updated_at_index_exists(self, temp_db):
        import database.db_service as db_mod
        old_path = db_mod.DB_PATH
        old_pool = db_mod._db_pool
        db_mod.DB_PATH = temp_db
        db_mod._db_pool = None
        try:
            DatabaseService()
            pool = await db_mod.get_db_pool()
            conn = await pool.acquire()
            try:
                cursor = await conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_canvases_updated'"
                )
                row = await cursor.fetchone()
                assert row is not None, "Index idx_canvases_updated does not exist"
            finally:
                await pool.release(conn)
        finally:
            db_mod.DB_PATH = old_path
            if db_mod._db_pool:
                await db_mod._db_pool.close_all()
            db_mod._db_pool = old_pool
