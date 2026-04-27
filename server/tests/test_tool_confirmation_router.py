import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


class TestToolConfirmationRouter:
    @pytest.fixture
    def mock_services(self):
        with patch('web.routers.tool_confirmation_router.tool_confirmation_manager') as mock_mgr, \
             patch('web.routers.tool_confirmation_router.send_to_websocket') as mock_ws:
            mock_mgr.confirm_tool = MagicMock(return_value=True)
            mock_mgr.cancel_confirmation = MagicMock(return_value=True)
            mock_ws.return_value = None
            yield {'mgr': mock_mgr, 'ws': mock_ws}

    def test_confirm_tool_success(self, mock_services):
        from web.routers.tool_confirmation_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.post('/api/tool_confirmation', json={
            'session_id': 's1',
            'tool_call_id': 't1',
            'confirmed': True
        })
        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_cancel_tool_success(self, mock_services):
        from web.routers.tool_confirmation_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.post('/api/tool_confirmation', json={
            'session_id': 's1',
            'tool_call_id': 't1',
            'confirmed': False
        })
        assert response.status_code == 200

    def test_confirm_tool_not_found(self):
        with patch('web.routers.tool_confirmation_router.tool_confirmation_manager') as mock_mgr, \
             patch('web.routers.tool_confirmation_router.send_to_websocket') as mock_ws:
            mock_mgr.confirm_tool.return_value = False
            mock_mgr.cancel_confirmation.return_value = True
            mock_ws.return_value = None
            from web.routers.tool_confirmation_router import router
            from fastapi import FastAPI
            app = FastAPI()
            app.include_router(router)
            client = TestClient(app)
            response = client.post('/api/tool_confirmation', json={
                'session_id': 's1',
                'tool_call_id': 'nonexistent',
                'confirmed': True
            })
            assert 'Tool call not found' in response.json()['detail']
