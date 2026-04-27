import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestContextInfo:
    def test_context_info_is_typed_dict(self):
        from agents.langgraph_service.agent_service import ContextInfo
        info: ContextInfo = {
            'canvas_id': 'canvas_1',
            'session_id': 'session_1',
            'model_info': {}
        }
        assert info['canvas_id'] == 'canvas_1'


class TestFixChatHistory:
    def test_empty_messages_returns_empty(self):
        from agents.langgraph_service.agent_service import _fix_chat_history
        result = _fix_chat_history([])
        assert result == []

    def test_passes_through_non_assistant_messages(self):
        from agents.langgraph_service.agent_service import _fix_chat_history
        messages = [
            {'role': 'user', 'content': 'hello'}
        ]
        result = _fix_chat_history(messages)
        assert len(result) == 1
        assert result[0]['role'] == 'user'

    def test_removes_orphaned_tool_calls(self):
        from agents.langgraph_service.agent_service import _fix_chat_history
        messages = [
            {'role': 'assistant', 'content': '', 'tool_calls': [{'id': 'call_1'}, {'id': 'call_2'}]},
            {'role': 'tool', 'tool_call_id': 'call_1', 'content': 'result1'}
        ]
        result = _fix_chat_history(messages)
        assert len(result) == 2
        assert result[0]['tool_calls'][0]['id'] == 'call_1'
        assert len(result[0]['tool_calls']) == 1

    def test_keeps_messages_without_tool_calls(self):
        from agents.langgraph_service.agent_service import _fix_chat_history
        messages = [
            {'role': 'assistant', 'content': 'hello', 'tool_calls': [{'id': 'call_1'}]},
            {'role': 'tool', 'tool_call_id': 'call_1', 'content': 'result1'}
        ]
        result = _fix_chat_history(messages)
        assert len(result) == 2

    def test_removes_orphaned_tool_calls_but_keeps_content(self):
        from agents.langgraph_service.agent_service import _fix_chat_history
        messages = [
            {'role': 'assistant', 'content': 'thinking', 'tool_calls': [{'id': 'orphan_call'}]}
        ]
        result = _fix_chat_history(messages)
        assert len(result) == 1
        assert result[0]['content'] == 'thinking'
        assert 'tool_calls' not in result[0]


class TestLanggraphMultiAgent:
    @pytest.mark.asyncio
    async def test_langgraph_multi_agent_function_exists(self):
        from agents.langgraph_service.agent_service import langgraph_multi_agent
        assert callable(langgraph_multi_agent)


class TestCreateTextModel:
    def test_create_text_model_function_exists(self):
        from agents.langgraph_service.agent_service import _create_text_model
        assert callable(_create_text_model)


class TestHandleError:
    @pytest.mark.asyncio
    async def test_handle_error_sends_websocket(self):
        from agents.langgraph_service.agent_service import _handle_error
        with patch('agents.langgraph_service.agent_service.send_to_websocket') as mock_ws:
            mock_ws.return_value = None
            await _handle_error(Exception("test error"), 'test_session')
            mock_ws.assert_called_once()
            call_args = mock_ws.call_args[0]
            assert call_args[0] == 'test_session'
            assert call_args[1]['type'] == 'error'
            assert 'test error' in call_args[1]['error']
