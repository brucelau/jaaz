import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestCreateJaazResponse:
    @pytest.mark.asyncio
    async def test_returns_not_found_when_no_image_content(self):
        from services.openai_agents_service import create_jaaz_response
        messages = [{'role': 'user', 'content': 'Hello'}]
        result = await create_jaaz_response(messages)
        assert 'not found input image' in str(result)

    @pytest.mark.asyncio
    async def test_returns_not_found_when_empty_content(self):
        from services.openai_agents_service import create_jaaz_response
        messages = [{'role': 'user', 'content': []}]
        result = await create_jaaz_response(messages)
        assert 'not found input image' in str(result)

    @pytest.mark.asyncio
    async def test_returns_not_found_when_no_image_url(self):
        from services.openai_agents_service import create_jaaz_response
        messages = [{'role': 'user', 'content': [{'type': 'text', 'text': 'hello'}]}]
        result = await create_jaaz_response(messages)
        assert 'not found input image' in str(result)

    @pytest.mark.asyncio
    async def test_handles_text_content_in_list(self):
        from services.openai_agents_service import create_jaaz_response
        messages = [{'role': 'user', 'content': [{'type': 'text', 'text': 'hello'}]}]
        result = await create_jaaz_response(messages)
        assert 'not found input image' in str(result)


class TestOpenaiAgentsServiceImport:
    def test_create_jaaz_response_is_callable(self):
        from services.openai_agents_service import create_jaaz_response
        assert callable(create_jaaz_response)

    def test_module_exports_create_jaaz_response(self):
        from services.openai_agents_service import __all__
        assert 'create_jaaz_response' in __all__
