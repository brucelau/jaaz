import pytest
import asyncio
import tempfile
import os
from services.db_service import DatabaseService, ConnectionPool, get_db_pool, DB_PATH


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.unlink(path)
    original_path = DatabaseService.__new__(DatabaseService)
    original_path.db_path = path
    original_path.db_path
    yield path
    if os.path.exists(path):
        os.unlink(path)


@pytest.fixture
def db_pool(temp_db):
    pool = ConnectionPool(temp_db, min_connections=1, max_connections=3)
    yield pool
    asyncio.run(pool.close_all())


class TestConnectionPool:
    @pytest.mark.asyncio
    async def test_initialize_creates_min_connections(self, temp_db):
        pool = ConnectionPool(temp_db, min_connections=2, max_connections=5)
        await pool.initialize()
        assert pool._initialized is True
        assert len(pool._pool) == 2
        await pool.close_all()

    @pytest.mark.asyncio
    async def test_acquire_returns_connection(self, temp_db):
        pool = ConnectionPool(temp_db)
        conn = await pool.acquire()
        assert conn is not None
        await pool.close_all()

    @pytest.mark.asyncio
    async def test_release_returns_connection_to_pool(self, temp_db):
        pool = ConnectionPool(temp_db, min_connections=0, max_connections=2)
        await pool.initialize()
        conn = await pool.acquire()
        await pool.release(conn)
        assert len(pool._pool) == 1
        await pool.close_all()

    @pytest.mark.asyncio
    async def test_release_closes_when_pool_full(self, temp_db):
        pool = ConnectionPool(temp_db, min_connections=0, max_connections=1)
        await pool.initialize()
        conn = await pool.acquire()
        await pool.release(conn)
        conn2 = await pool.acquire()
        assert len(pool._pool) == 0
        await conn.close()
        await conn2.close()
        await pool.close_all()

    @pytest.mark.asyncio
    async def test_exec_returns_cursor_and_connection(self, temp_db):
        pool = ConnectionPool(temp_db)
        cursor, conn = await pool.exec("SELECT 1 as a")
        row = await cursor.fetchone()
        assert row[0] == 1
        await conn.close()
        await pool.close_all()

    @pytest.mark.asyncio
    async def test_commit_and_release(self, temp_db):
        pool = ConnectionPool(temp_db)
        cursor, conn = await pool.exec("CREATE TABLE test (id INTEGER PRIMARY KEY)")
        await pool.commit_and_release(conn)
        assert len(pool._pool) == 1

    @pytest.mark.asyncio
    async def test_close_all_closes_all_connections(self, temp_db):
        pool = ConnectionPool(temp_db, min_connections=3, max_connections=5)
        await pool.initialize()
        await pool.close_all()
        assert len(pool._pool) == 0
        assert pool._initialized is False

    @pytest.mark.asyncio
    async def test_get_db_pool_returns_same_instance(self):
        global _test_pool
        _test_pool = None
        import services.db_service as db_mod
        db_mod._db_pool = None
        db_mod.DB_PATH = ":memory:"
        pool1 = await get_db_pool()
        pool2 = await get_db_pool()
        assert pool1 is pool2
        await pool1.close()
        db_mod._db_pool = None


class TestDatabaseService:
    @pytest.mark.asyncio
    async def test_create_and_list_canvases(self):
        import services.db_service as db_mod
        old_path = db_mod.DB_PATH
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(path)
        db_mod.DB_PATH = path
        db_mod._db_pool = None
        try:
            service = DatabaseService()
            await service.create_canvas("test_c1", "Test Canvas")
            canvases = await service.list_canvases()
            test_canvas = next((c for c in canvases if c["id"] == "test_c1"), None)
            assert test_canvas is not None
            assert test_canvas["name"] == "Test Canvas"
        finally:
            db_mod.DB_PATH = old_path
            db_mod._db_pool = None
            if os.path.exists(path):
                os.unlink(path)

    @pytest.mark.asyncio
    async def test_save_and_get_canvas_data(self):
        import services.db_service as db_mod
        old_path = db_mod.DB_PATH
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(path)
        db_mod.DB_PATH = path
        db_mod._db_pool = None
        try:
            service = DatabaseService()
            await service.create_canvas("c1", "Test")
            await service.save_canvas_data("c1", '{"content": "test"}', "thumb.png")
            data = await service.get_canvas_data("c1")
            assert data is not None
            assert data["data"]["content"] == "test"
            assert data["name"] == "Test"
        finally:
            db_mod.DB_PATH = old_path
            db_mod._db_pool = None
            if os.path.exists(path):
                os.unlink(path)

    @pytest.mark.asyncio
    async def test_delete_canvas(self):
        import services.db_service as db_mod
        old_path = db_mod.DB_PATH
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(path)
        db_mod.DB_PATH = path
        db_mod._db_pool = None
        try:
            service = DatabaseService()
            await service.create_canvas("test_del", "To Delete")
            canvases = await service.list_canvases()
            assert any(c["id"] == "test_del" for c in canvases)
            await service.delete_canvas("test_del")
            canvases = await service.list_canvases()
            assert not any(c["id"] == "test_del" for c in canvases)
        finally:
            db_mod.DB_PATH = old_path
            db_mod._db_pool = None
            if os.path.exists(path):
                os.unlink(path)

    @pytest.mark.asyncio
    async def test_rename_canvas(self):
        import services.db_service as db_mod
        old_path = db_mod.DB_PATH
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(path)
        db_mod.DB_PATH = path
        db_mod._db_pool = None
        try:
            service = DatabaseService()
            await service.create_canvas("test_rename", "Original")
            await service.rename_canvas("test_rename", "Renamed")
            canvases = await service.list_canvases()
            renamed = next((c for c in canvases if c["id"] == "test_rename"), None)
            assert renamed is not None
            assert renamed["name"] == "Renamed"
        finally:
            db_mod.DB_PATH = old_path
            db_mod._db_pool = None
            if os.path.exists(path):
                os.unlink(path)

    @pytest.mark.asyncio
    async def test_chat_session_crud(self):
        import services.db_service as db_mod
        old_path = db_mod.DB_PATH
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(path)
        db_mod.DB_PATH = path
        db_mod._db_pool = None
        try:
            service = DatabaseService()
            await service.create_canvas("c1", "Test")
            await service.create_chat_session("s1", "gpt-4", "openai", "c1", "Test Session")
            sessions = await service.list_sessions("c1")
            assert len(sessions) == 1
            assert sessions[0]["id"] == "s1"
            assert sessions[0]["title"] == "Test Session"
        finally:
            db_mod.DB_PATH = old_path
            db_mod._db_pool = None
            if os.path.exists(path):
                os.unlink(path)

    @pytest.mark.asyncio
    async def test_create_and_get_message(self):
        import services.db_service as db_mod
        old_path = db_mod.DB_PATH
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(path)
        db_mod.DB_PATH = path
        db_mod._db_pool = None
        try:
            service = DatabaseService()
            await service.create_canvas("c1", "Test")
            await service.create_chat_session("s1", "gpt-4", "openai", "c1")
            await service.create_message("s1", "user", '{"content": "Hello"}')
            history = await service.get_chat_history("s1")
            assert len(history) == 1
            assert history[0]["content"] == "Hello"
        finally:
            db_mod.DB_PATH = old_path
            db_mod._db_pool = None
            if os.path.exists(path):
                os.unlink(path)

    @pytest.mark.asyncio
    async def test_comfy_workflow_crud(self):
        import services.db_service as db_mod
        old_path = db_mod.DB_PATH
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        os.unlink(path)
        db_mod.DB_PATH = path
        db_mod._db_pool = None
        try:
            service = DatabaseService()
            await service.create_comfy_workflow(
                "Test WF", '{"nodes": []}', "A test workflow", '{"input": "test"}', '{"output": "test"}'
            )
            workflows = await service.list_comfy_workflows()
            assert len(workflows) == 1
            assert workflows[0]["name"] == "Test WF"
            workflow = await service.get_comfy_workflow(1)
            assert "nodes" in workflow
            await service.delete_comfy_workflow(1)
            workflows = await service.list_comfy_workflows()
            assert len(workflows) == 0
        finally:
            db_mod.DB_PATH = old_path
            db_mod._db_pool = None
            if os.path.exists(path):
                os.unlink(path)
