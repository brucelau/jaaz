import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI


class TestChatRouterImports:
    """Test chat_router imports"""

    def test_chat_router_exists(self):
        from routers.chat_router import router
        assert router is not None

    def test_chat_endpoint_exists(self):
        from routers.chat_router import router, chat
        assert chat is not None

    def test_cancel_endpoint_exists(self):
        from routers.chat_router import router, cancel_chat
        assert cancel_chat is not None

    def test_magic_endpoint_exists(self):
        from routers.chat_router import router, magic
        assert magic is not None

    def test_cancel_magic_endpoint_exists(self):
        from routers.chat_router import router, cancel_magic
        assert cancel_magic is not None


class TestChatEndpoint:
    """Test /api/chat endpoint"""

    @pytest.fixture
    def app(self):
        from routers.chat_router import router
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_chat_returns_done_status(self, client):
        with patch('routers.chat_router.handle_chat', new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = None
            response = client.post('/api/chat', json={'messages': []})
            assert response.status_code == 200
            assert response.json() == {'status': 'done'}

    def test_chat_calls_handle_chat(self, client):
        with patch('routers.chat_router.handle_chat', new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = None
            data = {'messages': [{'role': 'user', 'content': 'hello'}], 'session_id': 'test'}
            client.post('/api/chat', json=data)
            mock_handle.assert_called_once()

    def test_chat_passes_data_to_handler(self, client):
        with patch('routers.chat_router.handle_chat', new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = None
            data = {'messages': [{'role': 'user', 'content': 'hello'}], 'session_id': 'test', 'canvas_id': 'c1'}
            client.post('/api/chat', json=data)
            call_args = mock_handle.call_args[0][0]
            assert call_args['session_id'] == 'test'
            assert call_args['canvas_id'] == 'c1'


class TestCancelChatEndpoint:
    """Test /api/cancel/{session_id} endpoint"""

    @pytest.fixture
    def app(self):
        from routers.chat_router import router
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_cancel_returns_cancelled_when_task_found(self, client):
        with patch('routers.chat_router.get_stream_task') as mock_get:
            mock_task = MagicMock()
            mock_task.done.return_value = False
            mock_get.return_value = mock_task

            response = client.post('/api/cancel/test_session_123')
            assert response.status_code == 200
            assert response.json() == {'status': 'cancelled'}

    def test_cancel_returns_not_found_when_no_task(self, client):
        with patch('routers.chat_router.get_stream_task') as mock_get:
            mock_get.return_value = None

            response = client.post('/api/cancel/nonexistent_session')
            assert response.status_code == 200
            assert response.json() == {'status': 'not_found_or_done'}

    def test_cancel_returns_not_found_when_task_done(self, client):
        with patch('routers.chat_router.get_stream_task') as mock_get:
            mock_task = MagicMock()
            mock_task.done.return_value = True
            mock_get.return_value = mock_task

            response = client.post('/api/cancel/completed_session')
            assert response.status_code == 200
            assert response.json() == {'status': 'not_found_or_done'}

    def test_cancel_calls_task_cancel(self, client):
        with patch('routers.chat_router.get_stream_task') as mock_get:
            mock_task = MagicMock()
            mock_task.done.return_value = False
            mock_get.return_value = mock_task

            client.post('/api/cancel/test_session')
            mock_task.cancel.assert_called_once()


class TestMagicEndpoint:
    """Test /api/magic endpoint"""

    @pytest.fixture
    def app(self):
        from routers.chat_router import router
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_magic_returns_done_status(self, client):
        with patch('routers.chat_router.handle_magic', new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = None
            response = client.post('/api/magic', json={'prompt': 'test'})
            assert response.status_code == 200
            assert response.json() == {'status': 'done'}

    def test_magic_calls_handle_magic(self, client):
        with patch('routers.chat_router.handle_magic', new_callable=AsyncMock) as mock_handle:
            mock_handle.return_value = None
            data = {'prompt': 'generate magic image', 'session_id': 'magic_1'}
            client.post('/api/magic', json=data)
            mock_handle.assert_called_once()


class TestCancelMagicEndpoint:
    """Test /api/magic/cancel/{session_id} endpoint"""

    @pytest.fixture
    def app(self):
        from routers.chat_router import router
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_cancel_magic_returns_cancelled_when_task_found(self, client):
        with patch('routers.chat_router.get_stream_task') as mock_get:
            mock_task = MagicMock()
            mock_task.done.return_value = False
            mock_get.return_value = mock_task

            response = client.post('/api/magic/cancel/magic_session_123')
            assert response.status_code == 200
            assert response.json() == {'status': 'cancelled'}

    def test_cancel_magic_returns_not_found_when_no_task(self, client):
        with patch('routers.chat_router.get_stream_task') as mock_get:
            mock_get.return_value = None

            response = client.post('/api/magic/cancel/nonexistent_magic_session')
            assert response.status_code == 200
            assert response.json() == {'status': 'not_found_or_done'}

    def test_cancel_magic_returns_not_found_when_task_done(self, client):
        with patch('routers.chat_router.get_stream_task') as mock_get:
            mock_task = MagicMock()
            mock_task.done.return_value = True
            mock_get.return_value = mock_task

            response = client.post('/api/magic/cancel/completed_magic_session')
            assert response.status_code == 200
            assert response.json() == {'status': 'not_found_or_done'}

    def test_cancel_magic_calls_task_cancel(self, client):
        with patch('routers.chat_router.get_stream_task') as mock_get:
            mock_task = MagicMock()
            mock_task.done.return_value = False
            mock_get.return_value = mock_task

            client.post('/api/magic/cancel/magic_session')
            mock_task.cancel.assert_called_once()
