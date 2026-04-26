import pytest
from unittest.mock import patch, AsyncMock, MagicMock


class TestMagicServiceImports:
    def test_handle_magic_function_exists(self):
        from services.magic_service import handle_magic
        assert callable(handle_magic)


class TestHandleMagic:
    @pytest.mark.asyncio
    async def test_creates_session_when_single_message(self):
        from services import magic_service
        with patch('services.magic_service.db_service') as mock_db, \
             patch('services.magic_service.create_jaaz_response') as mock_agent, \
             patch('services.magic_service.send_to_websocket') as mock_ws, \
             patch('services.magic_service.add_stream_task'), \
             patch('services.magic_service.remove_stream_task'):
            mock_db.create_chat_session = AsyncMock()
            mock_db.create_message = AsyncMock()
            mock_agent.return_value = {'role': 'assistant', 'content': 'result'}
            mock_ws.return_value = None

            data = {
                'messages': [{'role': 'user', 'content': 'hello'}],
                'session_id': 'test_session',
                'canvas_id': 'canvas_1'
            }
            await magic_service.handle_magic(data)
            mock_db.create_chat_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_does_not_create_session_when_multiple_messages(self):
        from services import magic_service
        with patch('services.magic_service.db_service') as mock_db, \
             patch('services.magic_service.create_jaaz_response') as mock_agent, \
             patch('services.magic_service.send_to_websocket') as mock_ws, \
             patch('services.magic_service.add_stream_task'), \
             patch('services.magic_service.remove_stream_task'):
            mock_db.create_chat_session = AsyncMock()
            mock_db.create_message = AsyncMock()
            mock_agent.return_value = {'role': 'assistant', 'content': 'result'}
            mock_ws.return_value = None

            data = {
                'messages': [
                    {'role': 'user', 'content': 'hello'},
                    {'role': 'assistant', 'content': 'hi'}
                ],
                'session_id': 'test_session',
                'canvas_id': 'canvas_1'
            }
            await magic_service.handle_magic(data)
            mock_db.create_chat_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_empty_messages(self):
        from services import magic_service
        with patch('services.magic_service.db_service') as mock_db, \
             patch('services.magic_service.create_jaaz_response') as mock_agent, \
             patch('services.magic_service.send_to_websocket') as mock_ws, \
             patch('services.magic_service.add_stream_task'), \
             patch('services.magic_service.remove_stream_task'):
            mock_db.create_message = AsyncMock()
            mock_agent.return_value = {'role': 'assistant', 'content': 'result'}
            mock_ws.return_value = None

            data = {
                'messages': [],
                'session_id': 'test_session',
                'canvas_id': 'canvas_1'
            }
            await magic_service.handle_magic(data)
            mock_db.create_chat_session.assert_not_called()
