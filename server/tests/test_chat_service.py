import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestChatServiceImports:
    def test_handle_chat_function_exists(self):
        from web.services.chat_service import handle_chat
        assert callable(handle_chat)


class TestChatServiceFunctions:
    def test_handle_chat_is_async(self):
        import inspect
        from web.services.chat_service import handle_chat
        assert inspect.iscoroutinefunction(handle_chat)


class TestFixChatHistory:
    def test_empty_messages_returns_empty(self):
        from agents.langgraph_service.agent_service import _fix_chat_history
        result = _fix_chat_history([])
        assert result == []

    def test_passes_through_non_assistant_messages(self):
        from agents.langgraph_service.agent_service import _fix_chat_history
        messages = [{'role': 'user', 'content': 'hello'}]
        result = _fix_chat_history(messages)
        assert len(result) == 1

    def test_removes_orphaned_tool_calls(self):
        from agents.langgraph_service.agent_service import _fix_chat_history
        messages = [
            {'role': 'assistant', 'content': '', 'tool_calls': [{'id': 'call_1'}, {'id': 'call_2'}]},
            {'role': 'tool', 'tool_call_id': 'call_1', 'content': 'result1'}
        ]
        result = _fix_chat_history(messages)
        assert len(result[0]['tool_calls']) == 1
        assert result[0]['tool_calls'][0]['id'] == 'call_1'

    def test_keeps_messages_without_tool_calls(self):
        from agents.langgraph_service.agent_service import _fix_chat_history
        messages = [
            {'role': 'assistant', 'content': 'hello'},
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

    def test_handles_multiple_valid_tool_calls(self):
        from agents.langgraph_service.agent_service import _fix_chat_history
        messages = [
            {'role': 'assistant', 'content': '', 'tool_calls': [{'id': 'call_1'}, {'id': 'call_2'}]},
            {'role': 'tool', 'tool_call_id': 'call_1', 'content': 'result1'},
            {'role': 'tool', 'tool_call_id': 'call_2', 'content': 'result2'}
        ]
        result = _fix_chat_history(messages)
        assert len(result[0]['tool_calls']) == 2
