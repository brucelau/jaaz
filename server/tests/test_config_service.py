import pytest
import os
import tempfile
import asyncio
from services.config_service import ConfigService, _env_models, DEFAULT_PROVIDERS_CONFIG, AppConfig


class TestEnvModels:
    def test_env_models_parses_csv(self):
        os.environ["TEST_MODELS"] = "model-a,model-b,model-c"
        result = _env_models("TEST_MODELS", "")
        assert result == {
            "model-a": {"type": "text"},
            "model-b": {"type": "text"},
            "model-c": {"type": "text"},
        }
        del os.environ["TEST_MODELS"]

    def test_env_models_strips_whitespace(self):
        os.environ["TEST_MODELS"] = " model-a , model-b "
        result = _env_models("TEST_MODELS", "")
        assert "model-a" in result
        assert "model-b" in result
        del os.environ["TEST_MODELS"]

    def test_env_models_empty_string(self):
        os.environ["TEST_MODELS"] = ""
        result = _env_models("TEST_MODELS", "default-model")
        assert result == {}

    def test_env_models_missing_key(self):
        result = _env_models("NONEXISTENT_KEY", "a,b,c")
        assert result == {"a": {"type": "text"}, "b": {"type": "text"}, "c": {"type": "text"}}

    def test_env_models_default_used(self):
        result = _env_models("NONEXISTENT_KEY", "x-model,y-model")
        assert "x-model" in result
        assert "y-model" in result


class TestConfigServiceInit:
    def test_default_config_has_required_providers(self):
        service = ConfigService()
        config = service.get_config()
        assert "minimax" in config
        assert "openai" in config
        assert "gemini" in config
        assert "comfyui" in config

    def test_default_config_url_is_set(self):
        service = ConfigService()
        config = service.get_config()
        assert config["openai"]["url"] == "https://api.openai.com/v1/"
        assert config["gemini"]["url"] == "https://generativelanguage.googleapis.com/"

    def test_default_config_models_not_empty(self):
        service = ConfigService()
        config = service.get_config()
        assert len(config["openai"]["models"]) > 0
        assert len(config["gemini"]["models"]) > 0

    def test_config_file_defaults_to_user_data(self):
        service = ConfigService()
        assert "config.toml" in service.config_file


class TestConfigServiceJaazUrl:
    def test_jaaz_url_uses_env_when_set(self):
        os.environ["BASE_API_URL"] = "https://custom.jaaz.app"
        service = ConfigService()
        url = service._get_jaaz_url()
        assert url == "https://custom.jaaz.app/api/v1/"
        del os.environ["BASE_API_URL"]

    def test_jaaz_url_defaults_to_production(self):
        if "BASE_API_URL" in os.environ:
            del os.environ["BASE_API_URL"]
        service = ConfigService()
        url = service._get_jaaz_url()
        assert url == "https://jaaz.app/api/v1/"

    def test_jaaz_url_strips_trailing_slash(self):
        os.environ["BASE_API_URL"] = "https://test.app///"
        service = ConfigService()
        url = service._get_jaaz_url()
        assert url == "https://test.app/api/v1/"
        del os.environ["BASE_API_URL"]


class TestConfigServiceUpdate:
    @pytest.mark.asyncio
    async def test_update_config_writes_toml(self):
        fd, path = tempfile.mkstemp(suffix=".toml")
        os.close(fd)
        os.unlink(path)
        service = ConfigService()
        service.config_file = path
        data: AppConfig = {"openai": {"models": {"gpt-4o": {"type": "text"}}}}
        result = await service.update_config(data)
        assert result["status"] == "success"
        assert os.path.exists(path)
        os.unlink(path)

    @pytest.mark.asyncio
    async def test_update_config_sets_jaaz_url(self):
        fd, path = tempfile.mkstemp(suffix=".toml")
        os.close(fd)
        os.unlink(path)
        service = ConfigService()
        service.config_file = path
        os.environ["BASE_API_URL"] = "https://update.test"
        data: AppConfig = {"jaaz": {"url": ""}, "openai": {"models": {}}}
        await service.update_config(data)
        config = service.get_config()
        assert config["jaaz"]["url"] == "https://update.test/api/v1/"
        del os.environ["BASE_API_URL"]
        os.unlink(path)

    @pytest.mark.asyncio
    async def test_update_config_returns_error_on_failure(self):
        service = ConfigService()
        service.config_file = "/nonexistent/directory/config.toml"
        data: AppConfig = {"openai": {"models": {}}}
        result = await service.update_config(data)
        assert result["status"] == "error"


class TestConfigServiceExists:
    def test_exists_config_returns_true_when_file_exists(self):
        fd, path = tempfile.mkstemp(suffix=".toml")
        os.close(fd)
        service = ConfigService()
        service.config_file = path
        assert service.exists_config() is True
        os.unlink(path)

    def test_exists_config_returns_false_when_file_missing(self):
        service = ConfigService()
        service.config_file = "/nonexistent/path/config.toml"
        assert service.exists_config() is False


class TestDefaultProvidersModels:
    def test_default_minimax_models(self):
        service = ConfigService()
        models = service.get_config()["minimax"]["models"]
        assert "MiniMax-M2.5-highspeed" in models or "MiniMax-M2.7-highspeed" in models

    def test_default_openai_models(self):
        service = ConfigService()
        models = service.get_config()["openai"]["models"]
        assert "gpt-4o" in models or "gpt-4o-mini" in models

    def test_default_gemini_models(self):
        service = ConfigService()
        models = service.get_config()["gemini"]["models"]
        assert any("gemini" in m for m in models)
