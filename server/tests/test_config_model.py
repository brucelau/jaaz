import pytest
from pydantic import ValidationError
from models.config_model import LLMConfig, ConfigUpdate, ModelInfo


class TestLLMConfig:
    def test_valid_llm_config(self):
        config = LLMConfig(
            model="gpt-4",
            base_url="https://api.openai.com",
            api_key="sk-test",
            max_tokens=1000,
            temperature=0.7
        )
        assert config.model == "gpt-4"
        assert config.max_tokens == 1000

    def test_llm_config_defaults(self):
        config = LLMConfig(
            model="gpt-4",
            base_url="https://api.openai.com",
            api_key="sk-test",
            max_tokens=1000,
            temperature=0.7
        )
        assert config.temperature == 0.7

    def test_llm_config_required_fields(self):
        with pytest.raises(ValidationError):
            LLMConfig(model="gpt-4", base_url="https://api.openai.com")


class TestModelInfo:
    def test_valid_model_info(self):
        info = ModelInfo(
            provider="openai",
            model="gpt-4",
            url="https://api.openai.com",
            type="text"
        )
        assert info.provider == "openai"
        assert info.type == "text"

    def test_model_info_all_types(self):
        for model_type in ["text", "image", "tool", "video"]:
            info = ModelInfo(
                provider="test",
                model="test-model",
                url="https://test.com",
                type=model_type
            )
            assert info.type == model_type

    def test_model_info_invalid_type(self):
        with pytest.raises(ValidationError):
            ModelInfo(
                provider="test",
                model="test-model",
                url="https://test.com",
                type="invalid"
            )

    def test_model_info_required_fields(self):
        with pytest.raises(ValidationError):
            ModelInfo(provider="test")


class TestConfigUpdate:
    def test_valid_config_update(self):
        update = ConfigUpdate(
            llm=LLMConfig(
                model="gpt-4",
                base_url="https://api.openai.com",
                api_key="sk-test",
                max_tokens=1000,
                temperature=0.7
            )
        )
        assert update.llm.model == "gpt-4"

    def test_config_update_requires_llm(self):
        with pytest.raises(ValidationError):
            ConfigUpdate()
