import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import FastAPI
from io import BytesIO
from contextlib import asynccontextmanager


class TestImageRouterImports:
    """Test image_router imports"""

    def test_router_exists(self):
        from routers.image_router import router
        assert router is not None

    def test_upload_image_exists(self):
        from routers.image_router import router, upload_image
        assert upload_image is not None

    def test_get_file_exists(self):
        from routers.image_router import router, get_file
        assert get_file is not None

    def test_get_object_info_exists(self):
        from routers.image_router import router, get_object_info
        assert get_object_info is not None

    def test_compress_image_exists(self):
        from routers.image_router import compress_image
        assert compress_image is not None


class TestUploadImageEndpoint:
    """Test /api/upload_image endpoint"""

    @pytest.fixture
    def app(self):
        from routers.image_router import router
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    @pytest.fixture
    def mock_files_dir(self, tmp_path):
        return str(tmp_path)

    def test_upload_image_requires_file(self, client):
        response = client.post('/api/upload_image')
        assert response.status_code == 422  # Validation error

    def test_upload_image_returns_file_info(self, client):
        with patch('routers.image_router.FILES_DIR', '/tmp/test_files'), \
             patch('routers.image_router.generate_file_id', return_value='test_id_123'):
            # Create a minimal valid image
            from PIL import Image
            img = Image.new('RGB', (100, 100), color='red')
            img_bytes = BytesIO()
            img.save(img_bytes, format='JPEG')
            img_bytes.seek(0)

            with patch('routers.image_router.run_in_threadpool', new_callable=AsyncMock):
                response = client.post(
                    '/api/upload_image',
                    files={'file': ('test.jpg', img_bytes, 'image/jpeg')}
                )
                assert response.status_code == 200
                data = response.json()
                assert 'file_id' in data
                assert 'url' in data
                assert 'width' in data
                assert 'height' in data


class TestGetFileEndpoint:
    """Test /api/file/{file_id} endpoint"""

    @pytest.fixture
    def app(self):
        from routers.image_router import router
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_get_file_returns_404_when_not_found(self, client):
        with patch('routers.image_router.os.path.exists', return_value=False):
            response = client.get('/api/file/nonexistent_file.jpg')
            assert response.status_code == 404

    def test_get_file_returns_file_response(self, client):
        with patch('routers.image_router.os.path.exists', return_value=True), \
             patch('routers.image_router.FileResponse') as mock_response:
            mock_response.return_value = {"file": "content"}
            response = client.get('/api/file/existing_file.jpg')
            assert response.status_code == 200


class TestGetObjectInfoEndpoint:
    """Test /api/comfyui/object_info endpoint"""

    @pytest.fixture
    def app(self):
        from routers.image_router import router
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        return TestClient(app)

    def test_object_info_requires_url(self, client):
        response = client.post('/api/comfyui/object_info', json={})
        assert response.status_code == 400
        assert 'URL is required' in response.json()['detail']

    def test_object_info_returns_data_on_success(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'nodes': []}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        @asynccontextmanager
        async def mock_create(*args, **kwargs):
            yield mock_client

        with patch('routers.image_router.HttpClient.create', new=mock_create):
            response = client.post(
                '/api/comfyui/object_info',
                json={'url': 'http://localhost:8188'}
            )
            assert response.status_code == 200
            assert 'nodes' in response.json()

    def test_object_info_returns_503_on_connection_error(self, client):
        from httpx import ConnectError

        @asynccontextmanager
        async def mock_create(*args, **kwargs):
            mock_client = MagicMock()
            mock_client.get = AsyncMock(side_effect=ConnectError("Connection refused"))
            yield mock_client

        with patch('routers.image_router.HttpClient.create', new=mock_create):
            response = client.post(
                '/api/comfyui/object_info',
                json={'url': 'http://localhost:8188'}
            )
            assert response.status_code == 503
            assert 'not available' in response.json()['detail']


class TestCompressImage:
    """Test compress_image helper function"""

    def test_compress_image_returns_bytes(self):
        from routers.image_router import compress_image
        from PIL import Image

        img = Image.new('RGB', (100, 100), color='red')
        result = compress_image(img, max_size_mb=0.001)  # Very small size
        assert isinstance(result, bytes)

    def test_compress_image_handles_large_image(self):
        from routers.image_router import compress_image
        from PIL import Image

        # Create a large image
        img = Image.new('RGB', (2000, 2000), color='blue')
        result = compress_image(img, max_size_mb=0.1)
        assert isinstance(result, bytes)

    def test_compress_image_preserves_aspect_ratio(self):
        from routers.image_router import compress_image
        from PIL import Image

        # Create a non-square image
        img = Image.new('RGB', (2000, 1000), color='green')
        result = compress_image(img, max_size_mb=0.1)
        assert isinstance(result, bytes)

    def test_compress_image_returns_jpeg_format(self):
        from routers.image_router import compress_image
        from PIL import Image
        from io import BytesIO

        img = Image.new('RGB', (100, 100), color='yellow')
        result = compress_image(img, max_size_mb=0.1)

        # Verify it's a valid JPEG
        with Image.open(BytesIO(result)) as verified_img:
            assert verified_img.format == 'JPEG'
