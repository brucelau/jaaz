import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestRootRouterImports:
    def test_router_exists(self):
        from routers.root_router import router
        assert router is not None

    def test_get_ollama_model_list_function_exists(self):
        from routers.root_router import get_ollama_model_list
        assert callable(get_ollama_model_list)

    def test_get_comfyui_model_list_function_exists(self):
        from routers.root_router import get_comfyui_model_list
        assert callable(get_comfyui_model_list)


class TestGetModels:
    @pytest.mark.asyncio
    @patch('routers.root_router.config_service')
    @patch('routers.root_router.get_ollama_model_list')
    async def test_get_models_returns_list(self, mock_ollama, mock_config):
        from routers.root_router import get_models
        mock_config.get_config.return_value = {
            'openai': {
                'url': 'https://api.openai.com',
                'api_key': 'sk-test',
                'models': {'gpt-4': {'type': 'text'}}
            }
        }
        mock_ollama.return_value = []
        result = await get_models()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    @patch('routers.root_router.get_ollama_model_list')
    async def test_get_models_skips_empty_api_key(self, mock_ollama):
        from routers.root_router import get_models
        with patch('routers.root_router.config_service') as mock_config:
            mock_config.get_config.return_value = {
                'openai': {
                    'url': 'https://api.openai.com',
                    'api_key': '',
                    'models': {'gpt-4': {'type': 'text'}}
                }
            }
            mock_ollama.return_value = []
            result = await get_models()
            assert len(result) == 0


class TestListTools:
    @pytest.mark.asyncio
    @patch('routers.root_router.tool_service')
    @patch('routers.root_router.config_service')
    async def test_list_tools_returns_list(self, mock_config, mock_tool_service):
        from routers.root_router import list_tools
        mock_tool_service.tools = {
            'test_tool': {'provider': 'openai', 'type': 'text', 'display_name': 'Test'}
        }
        mock_config.get_config.return_value = {
            'openai': {'api_key': 'sk-test'}
        }
        result = await list_tools()
        assert isinstance(result, list)

    @pytest.mark.asyncio
    @patch('routers.root_router.tool_service')
    @patch('routers.root_router.config_service')
    async def test_list_tools_skips_system_tools(self, mock_config, mock_tool_service):
        from routers.root_router import list_tools
        mock_tool_service.tools = {
            'internal_tool': {'provider': 'system', 'type': 'text'},
            'user_tool': {'provider': 'openai', 'type': 'text'}
        }
        mock_config.get_config.return_value = {
            'openai': {'api_key': 'sk-test'}
        }
        result = await list_tools()
        assert len(result) == 1


class TestChatSessions:
    @patch('routers.root_router.db_service')
    @pytest.mark.asyncio
    async def test_list_chat_sessions(self, mock_db):
        from routers.root_router import list_chat_sessions
        mock_db.list_sessions = AsyncMock(return_value=[{'id': 'session1'}])
        result = await list_chat_sessions()
        assert result == [{'id': 'session1'}]

    @patch('routers.root_router.db_service')
    @pytest.mark.asyncio
    async def test_get_chat_session(self, mock_db):
        from routers.root_router import get_chat_session
        mock_db.get_chat_history = AsyncMock(return_value=[{'role': 'user', 'content': 'hello'}])
        result = await get_chat_session('test_session')
        assert len(result) == 1


class TestBilling:
    @pytest.mark.asyncio
    async def test_get_balance_returns_high_balance(self):
        from routers.root_router import get_balance
        result = await get_balance()
        assert result == {"balance": "999999.99"}
