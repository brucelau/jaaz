import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


class TestCanvasRouter:
    @pytest.fixture
    def mock_router(self):
        from routers import canvas_router
        mock_db = MagicMock()
        mock_db.list_canvases = AsyncMock(return_value=[])
        mock_db.create_canvas = AsyncMock(return_value=None)
        mock_db.get_canvas_data = AsyncMock(return_value={'data': {}})
        mock_db.save_canvas_data = AsyncMock(return_value=None)
        mock_db.rename_canvas = AsyncMock(return_value=None)
        mock_db.delete_canvas = AsyncMock(return_value=None)
        mock_chat = AsyncMock(return_value=None)
        with patch.object(canvas_router, 'db_service', mock_db), \
             patch.object(canvas_router, 'handle_chat', mock_chat):
            yield {'db': mock_db, 'chat': mock_chat, 'router': canvas_router.router}

    def test_list_canvases(self, mock_router):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(mock_router['router'])
        client = TestClient(app)
        mock_router['db'].list_canvases.return_value = [{'id': 'c1', 'name': 'Test'}]
        response = client.get('/api/canvas/list')
        assert response.status_code == 200

    def test_create_canvas(self, mock_router):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(mock_router['router'])
        client = TestClient(app)
        response = client.post('/api/canvas/create', json={'canvas_id': 'c1', 'name': 'Test'})
        assert response.status_code == 200
        assert response.json()['id'] == 'c1'

    def test_get_canvas(self, mock_router):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(mock_router['router'])
        client = TestClient(app)
        response = client.get('/api/canvas/c1')
        assert response.status_code == 200

    def test_save_canvas(self, mock_router):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(mock_router['router'])
        client = TestClient(app)
        response = client.post('/api/canvas/c1/save', json={'data': {}, 'thumbnail': ''})
        assert response.status_code == 200

    def test_rename_canvas(self, mock_router):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(mock_router['router'])
        client = TestClient(app)
        response = client.post('/api/canvas/c1/rename', json={'name': 'New Name'})
        assert response.status_code == 200

    def test_delete_canvas(self, mock_router):
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(mock_router['router'])
        client = TestClient(app)
        response = client.delete('/api/canvas/c1/delete')
        assert response.status_code == 200
