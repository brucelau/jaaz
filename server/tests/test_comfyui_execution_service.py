import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock
from web.services.comfyui_execution_service import check_comfy_server_running, upload_image

@pytest.mark.asyncio
async def test_check_comfy_server_running_success():
    mock_response = MagicMock()
    mock_response.status_code = 200

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    mock_client_ctx = AsyncMock()
    mock_client_ctx.__aenter__.return_value = mock_client

    with patch("web.services.comfyui_execution_service.HttpClient.create", return_value=mock_client_ctx):
        result = await check_comfy_server_running("http://localhost:8188")
        assert result is True

@pytest.mark.asyncio
async def test_check_comfy_server_running_failure():
    mock_response = MagicMock()
    mock_response.status_code = 500

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response

    mock_client_ctx = AsyncMock()
    mock_client_ctx.__aenter__.return_value = mock_client

    with patch("web.services.comfyui_execution_service.HttpClient.create", return_value=mock_client_ctx):
        result = await check_comfy_server_running("http://localhost:8188")
        assert result is False

@pytest.mark.asyncio
async def test_upload_image_success():
    mock_response = MagicMock()
    mock_response.json.return_value = {"name": "test_image.png"}

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response

    mock_client_ctx = AsyncMock()
    mock_client_ctx.__aenter__.return_value = mock_client

    with patch("web.services.comfyui_execution_service.HttpClient.create", return_value=mock_client_ctx):
        result = await upload_image(b"fake_image_data", "http://localhost:8188", filename="test.png")
        assert result == "jaaz/test_image.png"
