import pytest
import subprocess
import time
import os
import sys
from pathlib import Path
from unittest.mock import patch, AsyncMock

try:
    from playwright.sync_api import sync_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = object


SERVER_PORT = 57999
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"
SERVER_STARTUP_TIMEOUT = 30


def is_server_running(url: str) -> bool:
    """Check if server is already running"""
    try:
        import httpx
        response = httpx.get(f"{url}/api/list_models", timeout=2)
        return response.status_code == 200
    except:
        return False


@pytest.fixture(scope="module")
def backend_server():
    """Start the backend server for E2E tests if not already running"""
    if is_server_running(SERVER_URL):
        yield None
        return

    server_dir = Path(__file__).parent.parent
    env = os.environ.copy()
    env['UI_DIST_DIR'] = str(server_dir / 'react' / 'dist')

    process = subprocess.Popen(
        [sys.executable, '-m', 'uvicorn', 'main:socket_app', '--host', '127.0.0.1', '--port', str(SERVER_PORT)],
        cwd=str(server_dir),
        env=env
    )

    import httpx
    start_time = time.time()
    while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
        try:
            response = httpx.get(f"{SERVER_URL}/api/list_models", timeout=1)
            if response.status_code == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        process.terminate()
        process.wait(timeout=5)
        pytest.fail(f"Backend server failed to start within {SERVER_STARTUP_TIMEOUT}s")

    yield process

    process.terminate()
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        process.kill()


@pytest.fixture
def browser_page():
    """Provide a browser page for testing"""
    if not PLAYWRIGHT_AVAILABLE:
        pytest.skip("Playwright not available")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        yield page
        context.close()
        browser.close()


class TestImageGenerationE2E:
    """End-to-end smoke tests for image generation"""

    def test_server_is_running(self, backend_server):
        """Verify backend server is accessible"""
        import httpx
        response = httpx.get(f"{SERVER_URL}/api/list_models", timeout=5)
        assert response.status_code == 200

    def test_frontend_loads(self, backend_server, browser_page: Page):
        """Verify frontend loads and is accessible"""
        browser_page.goto(SERVER_URL, timeout=10000)
        browser_page.wait_for_load_state('networkidle', timeout=10000)

    def test_upload_image_api_directly(self, backend_server):
        """Test upload_image API directly via HTTP"""
        import httpx
        from io import BytesIO
        from PIL import Image

        img = Image.new('RGB', (200, 200), color='red')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        files = {'file': ('test.jpg', img_bytes, 'image/jpeg')}
        response = httpx.post(f"{SERVER_URL}/api/upload_image", files=files, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert 'file_id' in data
        assert 'url' in data

    def test_magic_endpoint_accessible(self, backend_server):
        """Test magic endpoint responds"""
        import httpx
        import uuid
        session_id = f"test_session_{uuid.uuid4().hex[:8]}"
        response = httpx.post(
            f"{SERVER_URL}/api/magic",
            json={
                'messages': [{'role': 'user', 'content': 'test'}],
                'session_id': session_id,
                'canvas_id': 'canvas_1'
            },
            timeout=5
        )
        assert response.status_code == 200
        assert response.json() == {'status': 'done'}

    def test_list_models_api(self, backend_server):
        """Test list_models API"""
        import httpx
        response = httpx.get(f"{SERVER_URL}/api/list_models", timeout=5)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_tools_api(self, backend_server):
        """Test list_tools API"""
        import httpx
        response = httpx.get(f"{SERVER_URL}/api/list_tools", timeout=5)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_cancel_magic_returns_proper_response(self, backend_server):
        """Test cancel magic endpoint"""
        import httpx
        response = httpx.post(
            f"{SERVER_URL}/api/magic/cancel/nonexistent_session",
            timeout=5
        )
        assert response.status_code == 200
        assert response.json() == {'status': 'not_found_or_done'}

    def test_full_image_generation_workflow(self, backend_server, browser_page: Page):
        """Test complete workflow: upload image -> submit generation task -> verify completion"""
        import httpx
        from io import BytesIO
        from PIL import Image
        import uuid

        session_id = f"e2e_session_{uuid.uuid4().hex[:8]}"
        canvas_id = f"e2e_canvas_{uuid.uuid4().hex[:8]}"

        img = Image.new('RGB', (400, 300), color='green')
        img_bytes = BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        upload_response = httpx.post(
            f"{SERVER_URL}/api/upload_image",
            files={'file': ('workflow_test.jpg', img_bytes, 'image/jpeg')},
            timeout=10
        )
        assert upload_response.status_code == 200
        upload_data = upload_response.json()
        assert 'file_id' in upload_data
        assert 'url' in upload_data
        uploaded_file_id = upload_data['file_id']

        messages = [
            {'role': 'user', 'content': f'Generate an image based on {uploaded_file_id}'}
        ]

        magic_response = httpx.post(
            f"{SERVER_URL}/api/magic",
            json={
                'messages': messages,
                'session_id': session_id,
                'canvas_id': canvas_id
            },
            timeout=30
        )
        assert magic_response.status_code == 200
        assert magic_response.json() == {'status': 'done'}

        verify_response = httpx.get(
            f"{SERVER_URL}/api/chat_session/{session_id}",
            timeout=5
        )
        assert verify_response.status_code == 200
        session_data = verify_response.json()
        assert isinstance(session_data, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
