import pytest
from pydantic import ValidationError
from models.tool_model import ToolInfo, ToolInfoJson


class TestToolInfo:
    def test_valid_tool_info(self):
        tool = ToolInfo(
            tool_function=lambda: None,
            provider="test_provider"
        )
        assert tool.provider == "test_provider"
        assert callable(tool.tool_function)

    def test_tool_info_optional_fields(self):
        tool = ToolInfo(
            tool_function=lambda: None,
            provider="test_provider",
            display_name="Test Tool",
            type="image"
        )
        assert tool.display_name == "Test Tool"
        assert tool.type == "image"

    def test_tool_info_defaults(self):
        tool = ToolInfo(
            tool_function=lambda: None,
            provider="test_provider"
        )
        assert tool.display_name is None
        assert tool.type is None

    def test_tool_info_required_fields(self):
        with pytest.raises(ValidationError):
            ToolInfo(provider="test")


class TestToolInfoJson:
    def test_valid_tool_info_json(self):
        info = ToolInfoJson(
            provider="openai",
            id="gpt-4"
        )
        assert info.provider == "openai"
        assert info.id == "gpt-4"

    def test_tool_info_json_optional_fields(self):
        info = ToolInfoJson(
            provider="openai",
            id="gpt-4",
            display_name="GPT-4",
            type="text"
        )
        assert info.display_name == "GPT-4"
        assert info.type == "text"

    def test_tool_info_json_defaults(self):
        info = ToolInfoJson(
            provider="openai",
            id="gpt-4"
        )
        assert info.display_name is None
        assert info.type is None

    def test_tool_info_json_required_fields(self):
        with pytest.raises(ValidationError):
            ToolInfoJson(provider="test")

    def test_tool_info_json_requires_id(self):
        with pytest.raises(ValidationError):
            ToolInfoJson(id="test-id")
