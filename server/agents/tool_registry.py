from typing import Dict, List, Any
from langchain_core.tools import BaseTool
from models.tool_model import ToolInfo
from web.services.log_service import tool_logger as logger


class ToolRegistry:
    """In-memory registry for tools. Handles storage and retrieval of tool metadata."""

    def __init__(self):
        self.tools: Dict[str, ToolInfo] = {}

    def register(self, tool_id: str, tool_info: ToolInfo) -> None:
        self.tools[tool_id] = tool_info

    def unregister(self, tool_id: str) -> None:
        self.tools.pop(tool_id, None)

    def get(self, tool_id: str) -> ToolInfo | None:
        return self.tools.get(tool_id)

    def get_tool_function(self, tool_id: str) -> BaseTool | None:
        tool_info = self.tools.get(tool_id)
        return tool_info.get("tool_function") if tool_info else None

    def get_all(self) -> Dict[str, ToolInfo]:
        return self.tools.copy()

    def get_by_provider(self, provider: str) -> Dict[str, ToolInfo]:
        return {
            tool_id: info
            for tool_id, info in self.tools.items()
            if info.get("provider") == provider
        }

    def get_system_tools(self) -> List[Any]:
        return [
            tool_info["tool_function"]
            for tool_info in self.tools.values()
            if tool_info.get("provider") == "system" and "tool_function" in tool_info
        ]

    def clear(self) -> None:
        self.tools.clear()

    def __len__(self) -> int:
        return len(self.tools)

    def __contains__(self, tool_id: str) -> bool:
        return tool_id in self.tools
