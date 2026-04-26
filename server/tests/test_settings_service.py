import pytest
import os
import tempfile
import asyncio
from unittest.mock import patch


class TestSettingsServiceInit:
    def test_default_settings_file_in_config_dir(self):
        from db.settings_service import SettingsService
        service = SettingsService()
        assert "settings.json" in service.settings_file

    def test_settings_file_env_override(self):
        with patch.dict(os.environ, {"SETTINGS_PATH": "/custom/path/settings.json"}):
            from db.settings_service import SettingsService
            service = SettingsService()
            assert service.settings_file == "/custom/path/settings.json"


class TestSettingsServiceDefaults:
    def test_default_settings_has_required_keys(self):
        from db.settings_service import DEFAULT_SETTINGS
        assert "proxy" in DEFAULT_SETTINGS
        assert "enabled_knowledge" in DEFAULT_SETTINGS
        assert "enabled_knowledge_data" in DEFAULT_SETTINGS

    def test_default_proxy_value(self):
        from db.settings_service import DEFAULT_SETTINGS
        assert DEFAULT_SETTINGS["proxy"] == "system"

    def test_default_knowledge_lists_empty(self):
        from db.settings_service import DEFAULT_SETTINGS
        assert DEFAULT_SETTINGS["enabled_knowledge"] == []
        assert DEFAULT_SETTINGS["enabled_knowledge_data"] == []


class TestSettingsServiceCRUD:
    @pytest.fixture
    def temp_settings_service(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        os.remove(path)
        with patch.dict(os.environ, {"SETTINGS_PATH": path}):
            from db.settings_service import SettingsService
            service = SettingsService()
            yield service
            if os.path.exists(path):
                os.remove(path)

    @pytest.mark.asyncio
    async def test_exists_settings_returns_false_when_missing(self, temp_settings_service):
        result = await temp_settings_service.exists_settings()
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_settings_returns_true_when_exists(self, temp_settings_service):
        temp_settings_service.create_default_settings()
        result = await temp_settings_service.exists_settings()
        assert result is True

    def test_get_settings_creates_default_if_missing(self, temp_settings_service):
        settings = temp_settings_service.get_settings()
        assert settings["proxy"] == "system"
        assert settings["enabled_knowledge"] == []
        assert settings["enabled_knowledge_data"] == []

    def test_get_raw_settings_creates_default_if_missing(self, temp_settings_service):
        settings = temp_settings_service.get_raw_settings()
        assert settings["proxy"] == "system"

    def test_get_proxy_config(self, temp_settings_service):
        proxy = temp_settings_service.get_proxy_config()
        assert proxy == "system"

    def test_get_enabled_knowledge_ids(self, temp_settings_service):
        ids = temp_settings_service.get_enabled_knowledge_ids()
        assert ids == []

    def test_get_enabled_knowledge_data(self, temp_settings_service):
        data = temp_settings_service.get_enabled_knowledge_data()
        assert data == []

    @pytest.mark.asyncio
    async def test_update_settings_success(self, temp_settings_service):
        result = await temp_settings_service.update_settings({"proxy": "http://proxy.com:8080"})
        assert result["status"] == "success"
        settings = temp_settings_service.get_raw_settings()
        assert settings["proxy"] == "http://proxy.com:8080"

    @pytest.mark.asyncio
    async def test_update_enabled_knowledge(self, temp_settings_service):
        result = await temp_settings_service.update_enabled_knowledge(["kb1", "kb2"])
        assert result["status"] == "success"
        ids = temp_settings_service.get_enabled_knowledge_ids()
        assert ids == ["kb1", "kb2"]

    @pytest.mark.asyncio
    async def test_update_enabled_knowledge_data(self, temp_settings_service):
        knowledge_data = [
            {"id": "kb1", "name": "Knowledge Base 1"},
            {"id": "kb2", "name": "Knowledge Base 2"}
        ]
        result = await temp_settings_service.update_enabled_knowledge_data(knowledge_data)
        assert result["status"] == "success"
        ids = temp_settings_service.get_enabled_knowledge_ids()
        assert ids == ["kb1", "kb2"]
        data = temp_settings_service.get_enabled_knowledge_data()
        assert data == knowledge_data

    @pytest.mark.asyncio
    async def test_update_settings_with_dict(self, temp_settings_service):
        temp_settings_service.create_default_settings()
        await temp_settings_service.update_settings({
            "enabled_knowledge": ["kb1", "kb2"]
        })
        settings = temp_settings_service.get_raw_settings()
        assert settings["enabled_knowledge"] == ["kb1", "kb2"]


class TestSettingsServiceErrorHandling:
    def test_get_settings_returns_defaults_on_error(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bad_path = os.path.join(tmpdir, "nonexistent", "settings.json")
            with patch.dict(os.environ, {"SETTINGS_PATH": bad_path}):
                from db.settings_service import SettingsService
                service = SettingsService()
                settings = service.get_settings()
                from db.settings_service import DEFAULT_SETTINGS
                assert settings == DEFAULT_SETTINGS
