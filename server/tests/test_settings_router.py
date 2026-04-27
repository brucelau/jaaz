import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


class TestSettingsRouter:
    @pytest.fixture
    def mock_services(self):
        with patch('web.routers.settings_router.settings_service') as mock_ss, \
             patch('web.routers.settings_router.db_service') as mock_db, \
             patch('web.routers.settings_router.tool_service') as mock_tool, \
             patch('web.routers.settings_router.list_user_enabled_knowledge') as mock_knowledge:
            mock_ss.exists_settings = AsyncMock(return_value=True)
            mock_ss.get_settings.return_value = {'proxy': 'system', 'enabled_knowledge': []}
            mock_ss.get_raw_settings.return_value = {'proxy': 'system'}
            mock_ss.update_settings = AsyncMock(return_value={'status': 'success'})
            mock_ss.get_proxy_config.return_value = 'system'
            mock_db.create_comfy_workflow = AsyncMock(return_value=None)
            mock_db.list_comfy_workflows = AsyncMock(return_value=[])
            mock_db.delete_comfy_workflow = AsyncMock(return_value={'success': True})
            mock_tool.initialize = AsyncMock(return_value=None)
            mock_knowledge.return_value = []
            yield {'ss': mock_ss, 'db': mock_db, 'tool': mock_tool, 'knowledge': mock_knowledge}

    def test_settings_exists(self, mock_services):
        from web.routers.settings_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get('/api/settings/exists')
        assert response.status_code == 200
        assert 'exists' in response.json()

    def test_get_settings(self, mock_services):
        from web.routers.settings_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get('/api/settings')
        assert response.status_code == 200

    def test_update_settings(self, mock_services):
        from web.routers.settings_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.post('/api/settings', json={'proxy': 'http://proxy.com:8080'})
        assert response.status_code == 200

    def test_get_proxy_status(self, mock_services):
        from web.routers.settings_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get('/api/settings/proxy/status')
        assert response.status_code == 200
        assert 'enable' in response.json()

    def test_get_proxy_settings(self, mock_services):
        from web.routers.settings_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get('/api/settings/proxy')
        assert response.status_code == 200
        assert 'proxy' in response.json()

    def test_update_proxy_settings(self, mock_services):
        from web.routers.settings_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.post('/api/settings/proxy', json={'proxy': 'no_proxy'})
        assert response.status_code == 200

    def test_update_proxy_invalid_format(self, mock_services):
        from web.routers.settings_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.post('/api/settings/proxy', json={'not_proxy': 'value'})
        assert response.status_code == 400

    def test_create_workflow(self, mock_services):
        from web.routers.settings_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.post('/api/settings/comfyui/create_workflow', json={
            'name': 'Test Workflow',
            'api_json': {'key': 'value'},
            'description': 'Test',
            'inputs': ['input1']
        })
        assert response.status_code == 200

    def test_list_workflows(self, mock_services):
        from web.routers.settings_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get('/api/settings/comfyui/list_workflows')
        assert response.status_code == 200

    def test_delete_workflow(self, mock_services):
        from web.routers.settings_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.delete('/api/settings/comfyui/delete_workflow/1')
        assert response.status_code == 200

    def test_get_enabled_knowledge(self, mock_services):
        from web.routers.settings_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        client = TestClient(app)
        response = client.get('/api/settings/knowledge/enabled')
        assert response.status_code == 200
        assert 'success' in response.json()
