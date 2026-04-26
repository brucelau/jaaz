import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient


class TestWorkspaceRouter:
    @pytest.fixture
    def temp_workspace(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_services(self):
        with patch('routers.workspace_router.USER_DATA_DIR', tempfile.gettempdir()):
            yield

    def test_get_file_type_image(self):
        from routers.workspace_router import get_file_type
        assert get_file_type('/path/to/image.jpg') == 'image'
        assert get_file_type('/path/to/photo.PNG') == 'image'

    def test_get_file_type_video(self):
        from routers.workspace_router import get_file_type
        assert get_file_type('/path/to/video.mp4') == 'video'
        assert get_file_type('/path/to/movie.MKV') == 'video'

    def test_get_file_type_audio(self):
        from routers.workspace_router import get_file_type
        assert get_file_type('/path/to/audio.mp3') == 'audio'

    def test_get_file_type_document(self):
        from routers.workspace_router import get_file_type
        assert get_file_type('/path/to/doc.pdf') == 'document'
        assert get_file_type('/path/to/text.txt') == 'document'

    def test_get_file_type_archive(self):
        from routers.workspace_router import get_file_type
        assert get_file_type('/path/to/archive.zip') == 'archive'

    def test_get_file_type_code(self):
        from routers.workspace_router import get_file_type
        assert get_file_type('/path/to/script.py') == 'code'
        assert get_file_type('/path/to/app.js') == 'code'

    def test_get_file_type_folder(self, tmp_path):
        from routers.workspace_router import get_file_type
        assert get_file_type(str(tmp_path)) == 'folder'

    def test_get_file_type_unknown(self):
        from routers.workspace_router import get_file_type
        assert get_file_type('/path/to/weird.xyz') == 'file'


class TestWorkspaceRouterEndpoints:
    def test_read_file_success(self, tmp_path):
        test_file = tmp_path / "test.md"
        test_file.write_text("# Hello")
        from routers.workspace_router import WORKSPACE_ROOT, router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        with patch('routers.workspace_router.WORKSPACE_ROOT', str(tmp_path)):
            client = TestClient(app)
            response = client.post('/api/read_file', json={'path': 'test.md'})
            assert response.status_code == 200
            assert 'content' in response.json()

    def test_read_file_not_found(self, tmp_path):
        from routers.workspace_router import router
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        with patch('routers.workspace_router.WORKSPACE_ROOT', str(tmp_path)):
            client = TestClient(app)
            response = client.post('/api/read_file', json={'path': 'nonexistent.md'})
            assert response.status_code == 200
            assert 'error' in response.json()
