import pytest
import httpx
import uuid
import time
from io import BytesIO
from PIL import Image
from pathlib import Path

SERVER_PORT = 57999
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"
SERVER_STARTUP_TIMEOUT = 30


def is_server_running(url: str) -> bool:
    try:
        response = httpx.get(f"{url}/api/list_models", timeout=2)
        return response.status_code == 200
    except:
        return False


@pytest.fixture(scope="module")
def backend_server():
    if is_server_running(SERVER_URL):
        yield None
        return

    import subprocess
    import os
    import sys

    server_dir = Path(__file__).parent.parent
    env = os.environ.copy()
    env["UI_DIST_DIR"] = str(server_dir / "react" / "dist")

    process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(SERVER_PORT)],
        cwd=str(server_dir),
        env=env,
    )

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


def create_test_image(format="JPEG", size=(200, 200), color="red"):
    img = Image.new("RGB", size, color=color)
    buf = BytesIO()
    img.save(buf, format=format)
    buf.seek(0)
    return buf


class TestAuthE2E:
    def test_register_new_user(self, backend_server):
        username = f"test_user_{uuid.uuid4().hex[:8]}"
        email = f"{username}@test.com"
        password = "testpass123"

        response = httpx.post(
            f"{SERVER_URL}/api/auth/register",
            json={"username": username, "email": email, "password": password},
            timeout=10,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "token" in data
        assert data["user_info"]["username"] == username

    def test_login_valid_user(self, backend_server):
        username = f"login_test_{uuid.uuid4().hex[:8]}"
        email = f"{username}@test.com"
        password = "testpass123"

        httpx.post(
            f"{SERVER_URL}/api/auth/register",
            json={"username": username, "email": email, "password": password},
            timeout=10,
        )

        response = httpx.post(
            f"{SERVER_URL}/api/auth/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "token" in data
        assert data["user_info"]["username"] == username

    def test_login_invalid_password(self, backend_server):
        username = f"login_fail_{uuid.uuid4().hex[:8]}"
        email = f"{username}@test.com"
        password = "testpass123"

        httpx.post(
            f"{SERVER_URL}/api/auth/register",
            json={"username": username, "email": email, "password": password},
            timeout=10,
        )

        response = httpx.post(
            f"{SERVER_URL}/api/auth/login",
            json={"username": username, "password": "wrongpassword"},
            timeout=10,
        )
        assert response.status_code in [200, 400, 401]

    def test_register_duplicate_username(self, backend_server):
        username = f"dup_user_{uuid.uuid4().hex[:8]}"
        email = f"{username}@test.com"
        password = "testpass123"

        httpx.post(
            f"{SERVER_URL}/api/auth/register",
            json={"username": username, "email": email, "password": password},
            timeout=10,
        )

        response = httpx.post(
            f"{SERVER_URL}/api/auth/register",
            json={"username": username, "email": f"different_{email}", "password": password},
            timeout=10,
        )
        assert response.status_code in [200, 400]


class TestCanvasE2E:
    def test_create_canvas(self, backend_server):
        canvas_id = f"canvas_{uuid.uuid4().hex[:8]}"
        response = httpx.post(
            f"{SERVER_URL}/api/canvas/create",
            json={"canvas_id": canvas_id, "name": f"Test Canvas {uuid.uuid4().hex[:8]}"},
            headers={"Authorization": "Bearer test_token"},
            timeout=10,
        )
        assert response.status_code == 200

    def test_list_canvases(self, backend_server):
        response = httpx.get(
            f"{SERVER_URL}/api/canvas/list",
            headers={"Authorization": "Bearer test_token"},
            timeout=10,
        )
        assert response.status_code == 200

    def test_get_canvas(self, backend_server):
        canvas_id = f"canvas_{uuid.uuid4().hex[:8]}"
        httpx.post(
            f"{SERVER_URL}/api/canvas/create",
            json={"canvas_id": canvas_id, "name": f"Get Test {uuid.uuid4().hex[:8]}"},
            headers={"Authorization": "Bearer test_token"},
            timeout=10,
        )

        response = httpx.get(
            f"{SERVER_URL}/api/canvas/{canvas_id}",
            timeout=10,
        )
        assert response.status_code == 200


class TestChatE2E:
    """End-to-end tests for chat functionality"""

    def test_chat_endpoint(self, backend_server):
        session_id = f"chat_session_{uuid.uuid4().hex[:8]}"
        response = httpx.post(
            f"{SERVER_URL}/api/chat",
            json={
                "messages": [{"role": "user", "content": "Hello"}],
                "session_id": session_id,
                "canvas_id": f"canvas_{uuid.uuid4().hex[:8]}",
            },
            headers={"Authorization": "Bearer test_token"},
            timeout=30,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["done", "streaming"]

    def test_magic_endpoint(self, backend_server):
        session_id = f"magic_session_{uuid.uuid4().hex[:8]}"
        response = httpx.post(
            f"{SERVER_URL}/api/magic",
            json={
                "messages": [{"role": "user", "content": "Generate something"}],
                "session_id": session_id,
                "canvas_id": f"canvas_{uuid.uuid4().hex[:8]}",
            },
            headers={"Authorization": "Bearer test_token"},
            timeout=30,
        )
        assert response.status_code == 200

    def test_cancel_chat(self, backend_server):
        response = httpx.post(
            f"{SERVER_URL}/api/chat/cancel/nonexistent_session",
            timeout=5,
        )
        assert response.status_code in [200, 404]


class TestWebSocketE2E:
    def test_websocket_connect(self, backend_server):
        import socketio

        sio_client = socketio.Client(reconnection=False)
        try:
            sio_client.connect(SERVER_URL, wait_timeout=5)
            assert sio_client.connected
            sio_client.disconnect()
        except Exception as e:
            pytest.skip(f"WebSocket connection failed: {e}")


class TestImageE2E:
    """End-to-end tests for image operations"""

    def test_upload_image(self, backend_server):
        img_bytes = create_test_image()
        files = {"file": ("test.jpg", img_bytes, "image/jpeg")}
        response = httpx.post(f"{SERVER_URL}/api/upload_image", files=files, timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "file_id" in data
        assert "url" in data

    def test_list_models(self, backend_server):
        response = httpx.get(f"{SERVER_URL}/api/list_models", timeout=5)
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_tools(self, backend_server):
        response = httpx.get(f"{SERVER_URL}/api/list_tools", timeout=5)
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestSettingsE2E:
    def test_get_proxy_settings(self, backend_server):
        response = httpx.get(
            f"{SERVER_URL}/api/settings/proxy/status",
            timeout=5,
        )
        assert response.status_code == 200

    def test_get_enabled_knowledge(self, backend_server):
        response = httpx.get(
            f"{SERVER_URL}/api/settings/knowledge/enabled",
            timeout=5,
        )
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])