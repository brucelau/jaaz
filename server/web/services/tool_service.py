from typing import Dict, List, Any
from langchain_core.tools import BaseTool
from models.tool_model import ToolInfo
from agents.tool_registry import ToolRegistry
from agents.tool_loader import ToolLoader
from agents.providers import PROVIDER_TOOLS


class ToolService:
    def __init__(self):
        self.registry = ToolRegistry()
        self._register_required_tools()

    def _register_required_tools(self):
        system_tools = ToolLoader.load_required_system_tools()
        for tool_id, tool_info in system_tools.items():
            self.registry.register(tool_id, tool_info)

    def register_tool(self, tool_id: str, tool_info: ToolInfo):
        self.registry.register(tool_id, tool_info)

    async def initialize(self):
        await ToolLoader.initialize(PROVIDER_TOOLS, self.registry)

    def get_tool(self, tool_name: str) -> BaseTool | None:
        return self.registry.get_tool_function(tool_name)

    def remove_tool(self, tool_id: str):
        self.registry.unregister(tool_id)

    def get_system_tools(self) -> List[Any]:
        return self.registry.get_system_tools()

    def get_all_tools(self) -> Dict[str, ToolInfo]:
        return self.registry.get_all()

    def clear_tools(self):
        self.registry.clear()
        self._register_required_tools()


tool_service = ToolService()
