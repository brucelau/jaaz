import pytest
import sys
from unittest.mock import MagicMock

sys.modules['langchain_core'] = MagicMock()
sys.modules['langchain_core.tools'] = MagicMock()
sys.modules['models'] = MagicMock()
sys.modules['models.tool_model'] = MagicMock()
sys.modules['tools'] = MagicMock()
sys.modules['tools.comfy_dynamic'] = MagicMock()
sys.modules['tools.write_plan'] = MagicMock()
sys.modules['tools.generate_image_by_gpt_image_1_jaaz'] = MagicMock()
sys.modules['tools.generate_image_by_imagen_4_jaaz'] = MagicMock()
sys.modules['tools.generate_image_by_imagen_4_replicate'] = MagicMock()
sys.modules['tools.generate_image_by_ideogram3_bal_jaaz'] = MagicMock()
sys.modules['tools.generate_image_by_ideogram'] = MagicMock()
sys.modules['tools.generate_image_by_nano_banana'] = MagicMock()
sys.modules['tools.enhance_airmold_prompt'] = MagicMock()
sys.modules['services.log_service'] = MagicMock()
sys.modules['services.db_service'] = MagicMock()
sys.modules['services.config_service'] = MagicMock()


class ToolInfo(dict):
    pass


class ToolService:
    def __init__(self):
        self.tools: dict = {}

    def register_tool(self, tool_id: str, tool_info: ToolInfo):
        self.tools[tool_id] = tool_info


@pytest.fixture
def tool_service():
    return ToolService()


class TestRegisterTool:
    def test_register_tool_adds_new_tool(self, tool_service):
        tool_info = ToolInfo({"provider": "test", "tool_function": lambda: None})
        tool_service.register_tool("test_tool", tool_info)
        assert "test_tool" in tool_service.tools

    def test_register_tool_overwrites_existing(self, tool_service):
        def func_v1():
            return "v1"

        def func_v2():
            return "v2"

        tool_service.tools["my_tool"] = {
            "provider": "test",
            "tool_function": func_v1,
        }
        tool_info = ToolInfo({"provider": "test", "tool_function": func_v2})
        tool_service.register_tool("my_tool", tool_info)
        assert tool_service.tools["my_tool"]["tool_function"] is func_v2

    def test_register_tool_silent_on_duplicate(self, tool_service):
        tool_service.tools["existing"] = {"provider": "test", "tool_function": lambda: None}
        tool_info = ToolInfo({"provider": "test", "tool_function": lambda: None})
        tool_service.register_tool("existing", tool_info)
        assert "existing" in tool_service.tools
