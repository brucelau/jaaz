import pytest


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
