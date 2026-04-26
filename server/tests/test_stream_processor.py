import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch


class TestStreamProcessorClass:
    def test_init_attributes(self):
        from services.langgraph_service.stream_processor import StreamProcessor
        mock_ws = AsyncMock()
        mock_db = MagicMock()
        processor = StreamProcessor('session_123', mock_db, mock_ws)

        assert processor.session_id == 'session_123'
        assert processor.db_service == mock_db
        assert processor.websocket_service == mock_ws
        assert processor.tool_calls == []
        assert processor.last_saved_message_index == 0
        assert processor.last_streaming_tool_call_id is None

    def test_tools_requiring_confirmation_default(self):
        from services.langgraph_service.stream_processor import StreamProcessor
        mock_ws = AsyncMock()
        mock_db = MagicMock()
        processor = StreamProcessor('session_123', mock_db, mock_ws)
        assert 'generate_video_by_veo3_fast_jaaz' in processor.TOOLS_REQUIRING_CONFIRMATION

    @pytest.mark.asyncio
    async def test_handle_chunk_values_type(self):
        from services.langgraph_service.stream_processor import StreamProcessor
        mock_ws = AsyncMock()
        mock_db = MagicMock()
        processor = StreamProcessor('session_123', mock_db, mock_ws)
        chunk = ('values', {'messages': []})
        await processor._handle_chunk(chunk)
        mock_ws.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_chunk_message_type(self):
        from services.langgraph_service.stream_processor import StreamProcessor
        from langchain_core.messages import AIMessageChunk
        mock_ws = AsyncMock()
        mock_db = MagicMock()
        processor = StreamProcessor('session_123', mock_db, mock_ws)
        chunk = ('messages', [AIMessageChunk(content='Hello')])
        await processor._handle_chunk(chunk)

    @pytest.mark.asyncio
    async def test_handle_tool_calls_sends_websocket(self):
        from services.langgraph_service.stream_processor import StreamProcessor
        mock_ws = AsyncMock()
        mock_db = MagicMock()
        processor = StreamProcessor('session_123', mock_db, mock_ws)
        tool_calls = [{'name': 'some_tool', 'id': 'call_123', 'args': {}}]
        await processor._handle_tool_calls(tool_calls)
        mock_ws.assert_called()

    @pytest.mark.asyncio
    async def test_handle_tool_calls_requires_confirmation_skipped(self):
        from services.langgraph_service.stream_processor import StreamProcessor
        mock_ws = AsyncMock()
        mock_db = MagicMock()
        processor = StreamProcessor('session_123', mock_db, mock_ws)
        processor.TOOLS_REQUIRING_CONFIRMATION = {'generate_video_by_veo3_fast_jaaz'}
        tool_calls = [{'name': 'generate_video_by_veo3_fast_jaaz', 'id': 'call_123', 'args': {}}]
        await processor._handle_tool_calls(tool_calls)
        assert mock_ws.call_count == 0

    @pytest.mark.asyncio
    async def test_handle_tool_call_chunks_with_args_only(self):
        from services.langgraph_service.stream_processor import StreamProcessor
        mock_ws = AsyncMock()
        mock_db = MagicMock()
        processor = StreamProcessor('session_123', mock_db, mock_ws)
        processor.last_streaming_tool_call_id = 'call_123'
        tool_call_chunks = [{'args': '{"prompt": "test"}'}]
        await processor._handle_tool_call_chunks(tool_call_chunks)
        mock_ws.assert_called_once()
        mock_ws.assert_called_with('session_123', {
            'type': 'tool_call_arguments',
            'id': 'call_123',
            'text': '{"prompt": "test"}'
        })

    @pytest.mark.asyncio
    async def test_handle_tool_call_chunks_sets_id(self):
        from services.langgraph_service.stream_processor import StreamProcessor
        mock_ws = AsyncMock()
        mock_db = MagicMock()
        processor = StreamProcessor('session_123', mock_db, mock_ws)
        processor.last_streaming_tool_call_id = None
        tool_call_chunks = [{'id': 'call_123', 'args': '{"prompt": "test"}'}]
        await processor._handle_tool_call_chunks(tool_call_chunks)
        assert processor.last_streaming_tool_call_id == 'call_123'
        mock_ws.assert_not_called()


class TestGetAttrOrDict:
    def test_get_attr_or_dict_from_dict(self):
        from services.langgraph_service.stream_processor import _get_attr_or_dict
        obj = {'name': 'test_name', 'args': {'prompt': 'hello'}}
        assert _get_attr_or_dict(obj, 'name') == 'test_name'
        assert _get_attr_or_dict(obj, 'args') == {'prompt': 'hello'}

    def test_get_attr_or_dict_from_object(self):
        from services.langgraph_service.stream_processor import _get_attr_or_dict
        class MockObj:
            name = 'obj_name'
            args = {'prompt': 'world'}
        obj = MockObj()
        assert _get_attr_or_dict(obj, 'name') == 'obj_name'
        assert _get_attr_or_dict(obj, 'args') == {'prompt': 'world'}

    def test_get_attr_or_dict_none_obj(self):
        from services.langgraph_service.stream_processor import _get_attr_or_dict
        assert _get_attr_or_dict(None, 'name') is None

    def test_get_attr_or_dict_missing_key(self):
        from services.langgraph_service.stream_processor import _get_attr_or_dict
        obj = {'name': 'test'}
        assert _get_attr_or_dict(obj, 'missing') is None

    def test_get_attr_or_dict_missing_attr(self):
        from services.langgraph_service.stream_processor import _get_attr_or_dict
        class MockObj:
            name = 'test'
        obj = MockObj()
        assert _get_attr_or_dict(obj, 'missing') is None


class TestToolsRequiringConfirmationEnv:
    def test_default_value(self):
        from services.langgraph_service.stream_processor import StreamProcessor
        assert 'generate_video_by_veo3_fast_jaaz' in StreamProcessor.TOOLS_REQUIRING_CONFIRMATION

    def test_class_attribute_is_set(self):
        from services.langgraph_service.stream_processor import StreamProcessor
        assert isinstance(StreamProcessor.TOOLS_REQUIRING_CONFIRMATION, set)
