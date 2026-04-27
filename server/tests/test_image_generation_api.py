import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from io import BytesIO
from PIL import Image


class TestImageGenerationAPI:
    @pytest.fixture
    def app(self):
        from web.routers.image_router import router as image_router
        from web.routers.chat_router import router as chat_router
        from web.routers.root_router import router as root_router

        app = FastAPI()
        app.include_router(image_router)
        app.include_router(chat_router)
        app.include_router(root_router)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_upload_image_returns_file_info(self, client):
        with patch('web.routers.image_router.FILES_DIR', '/tmp/test_files'), \
             patch('web.routers.image_router.generate_file_id', return_value='test_id_123'), \
             patch('web.routers.image_router.run_in_threadpool', new_callable=AsyncMock):

            img = Image.new('RGB', (100, 100), color='red')
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)

            response = client.post(
                '/api/upload_image',
                files={'file': ('test.jpg', img_bytes, 'image/jpeg')}
            )

            assert response.status_code == 200
            data = response.json()
            assert 'file_id' in data
            assert 'url' in data
            assert data['file_id'] == 'test_id_123.jpg'

    def test_upload_image_validates_required_file(self, client):
        response = client.post('/api/upload_image')
        assert response.status_code == 422

    def test_get_file_returns_transparent_png_for_missing_file(self, client):
        with patch('web.routers.image_router.os.path.exists', return_value=False):
            response = client.get('/api/file/nonexistent.jpg')
            assert response.status_code == 200
            assert response.headers['content-type'] == 'image/png'

    def test_list_models_endpoint_accessible(self, client):
        with patch('web.services.config_service.config_service') as mock_config:
            mock_config.get_config.return_value = {
                'openai': {
                    'url': 'https://api.openai.com',
                    'api_key': 'test_key',
                    'models': {'gpt-4': {'type': 'text'}}
                }
            }
            response = client.get('/api/list_models')
            assert response.status_code == 200

    def test_list_tools_endpoint_accessible(self, client):
        with patch('web.services.tool_service.tool_service') as mock_tool:
            mock_tool.tools = {
                'test_tool': {
                    'id': 'test_tool',
                    'provider': 'openai',
                    'type': 'image',
                    'display_name': 'Test Tool'
                }
            }
            response = client.get('/api/list_tools')
            assert response.status_code == 200


class TestMagicEndpoint:
    @pytest.fixture
    def app(self):
        from web.routers.chat_router import router as chat_router
        app = FastAPI()
        app.include_router(chat_router)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_magic_endpoint_returns_done(self, client):
        with patch('web.routers.chat_router.handle_magic', new_callable=AsyncMock) as mock:
            mock.return_value = None
            response = client.post('/api/magic', json={
                'messages': [{'role': 'user', 'content': 'generate image'}],
                'session_id': 'test_session',
                'canvas_id': 'canvas_1'
            }, headers={'Authorization': 'Bearer test_token'})
            assert response.status_code == 200
            assert response.json() == {'status': 'done'}

    def test_magic_cancel_returns_not_found_or_done(self, client):
        with patch('web.routers.chat_router.get_stream_task') as mock:
            mock.return_value = None
            response = client.post('/api/magic/cancel/nonexistent_session')
            assert response.status_code == 200
            assert response.json() == {'status': 'not_found_or_done'}


class TestImageGenerationFlow:
    """Test the complete image generation flow"""

    @pytest.fixture
    def app(self):
        from web.routers.image_router import router as image_router
        from web.routers.chat_router import router as chat_router
        from web.routers.root_router import router as root_router

        app = FastAPI()
        app.include_router(image_router)
        app.include_router(chat_router)
        app.include_router(root_router)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_upload_and_verify_image_flow(self, client):
        """Test uploading an image and verifying the response structure"""
        with patch('web.routers.image_router.FILES_DIR', '/tmp/test_files'), \
             patch('web.routers.image_router.generate_file_id', return_value='flow_test_id'), \
             patch('web.routers.image_router.run_in_threadpool', new_callable=AsyncMock):

            img = Image.new('RGB', (800, 600), color='blue')
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG', quality=95)
            img_bytes.seek(0)

            response = client.post(
                '/api/upload_image',
                files={'file': ('test_image.jpg', img_bytes, 'image/jpeg')}
            )

            assert response.status_code == 200
            data = response.json()

            assert 'file_id' in data
            assert 'url' in data
            assert 'width' in data
            assert 'height' in data
            assert data['width'] == 800
            assert data['height'] == 600

    def test_multiple_image_uploads_return_different_ids(self, client):
        """Test that multiple uploads get unique file IDs"""
        with patch('web.routers.image_router.FILES_DIR', '/tmp/test_files'), \
             patch('web.routers.image_router.generate_file_id', side_effect=['id_1', 'id_2']), \
             patch('web.routers.image_router.run_in_threadpool', new_callable=AsyncMock):

            img = Image.new('RGB', (100, 100), color='green')
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)

            response1 = client.post(
                '/api/upload_image',
                files={'file': ('img1.jpg', img_bytes, 'image/jpeg')}
            )

            img_bytes.seek(0)
            response2 = client.post(
                '/api/upload_image',
                files={'file': ('img2.jpg', img_bytes, 'image/jpeg')}
            )

            assert response1.json()['file_id'] != response2.json()['file_id']

    def test_comfyui_object_info_requires_url(self, client):
        """Test that object_info endpoint validates URL input"""
        response = client.post('/api/comfyui/object_info', json={})
        assert response.status_code == 400
        assert 'URL is required' in response.json()['detail']

    def test_chat_endpoint_structure(self, client):
        """Test chat endpoint accepts valid payload"""
        with patch('web.routers.chat_router.handle_chat', new_callable=AsyncMock) as mock:
            mock.return_value = None
            response = client.post('/api/chat', json={
                'messages': [
                    {'role': 'user', 'content': 'Create an image of a cat'}
                ],
                'session_id': 'test_session_123',
                'canvas_id': 'canvas_abc'
            }, headers={'Authorization': 'Bearer test_token'})
            assert response.status_code == 200
            assert response.json() == {'status': 'done'}
