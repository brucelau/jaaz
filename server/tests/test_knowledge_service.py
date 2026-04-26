import pytest
from unittest.mock import patch, MagicMock, AsyncMock


class TestKnowledgeService:
    def test_knowledge_service_instance_exists(self):
        from services.knowledge_service import knowledge_service
        assert knowledge_service is not None

    def test_list_user_enabled_knowledge_function_exists(self):
        from services.knowledge_service import list_user_enabled_knowledge
        assert callable(list_user_enabled_knowledge)

    @patch('services.knowledge_service.settings_service')
    def test_get_enabled_knowledge_ids(self, mock_settings):
        from services.knowledge_service import KnowledgeService
        mock_settings.get_enabled_knowledge_ids.return_value = ['kb1', 'kb2']
        service = KnowledgeService()
        result = service.get_enabled_knowledge_ids()
        assert result == ['kb1', 'kb2']

    @patch('services.knowledge_service.settings_service')
    def test_get_enabled_knowledge_data(self, mock_settings):
        from services.knowledge_service import KnowledgeService
        mock_settings.get_enabled_knowledge_data.return_value = [{'id': 'kb1', 'name': 'Test'}]
        service = KnowledgeService()
        result = service.get_enabled_knowledge_data()
        assert len(result) == 1

    @patch('services.knowledge_service.settings_service')
    def test_list_user_enabled_knowledge_formats_data(self, mock_settings):
        from services.knowledge_service import KnowledgeService
        mock_settings.get_enabled_knowledge_data.return_value = [
            {'id': 'kb1', 'name': 'Test KB', 'description': 'desc', 'content': 'content'}
        ]
        service = KnowledgeService()
        result = service.list_user_enabled_knowledge()
        assert len(result) == 1
        assert result[0]['id'] == 'kb1'
        assert result[0]['name'] == 'Test KB'

    @patch('services.knowledge_service.settings_service')
    def test_list_user_enabled_knowledge_handles_missing_fields(self, mock_settings):
        from services.knowledge_service import KnowledgeService
        mock_settings.get_enabled_knowledge_data.return_value = [
            {'id': 'kb1'}
        ]
        service = KnowledgeService()
        result = service.list_user_enabled_knowledge()
        assert result[0]['name'] == ''
        assert result[0]['description'] == ''
        assert result[0]['is_public'] is False

    @patch('services.knowledge_service.settings_service')
    def test_list_user_enabled_knowledge_empty(self, mock_settings):
        from services.knowledge_service import KnowledgeService
        mock_settings.get_enabled_knowledge_data.return_value = []
        service = KnowledgeService()
        result = service.list_user_enabled_knowledge()
        assert result == []

    @patch('services.knowledge_service.settings_service')
    @pytest.mark.asyncio
    async def test_update_enabled_knowledge_data(self, mock_settings):
        from services.knowledge_service import KnowledgeService
        mock_settings.update_enabled_knowledge_data = AsyncMock(return_value={'success': True})
        service = KnowledgeService()
        result = await service.update_enabled_knowledge_data([{'id': 'kb1'}])
        assert result == {'success': True}
