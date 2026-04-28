import os
import traceback
from typing import Dict, List
from models.tool_model import ToolInfo
from web.services.log_service import tool_logger as logger
from web.services.config_service import config_service
from database.db_service import db_service
from agents.tools.comfy_dynamic import build_tool


REQUIRED_SYSTEM_TOOLS = [
    ("write_plan", "agents.tools.write_plan", "write_plan_tool"),
    ("enhance_inflatable_prompt", "agents.tools.enhance_inflatable_prompt", "enhance_inflatable_prompt"),
    ("refine_inflatable_prompt", "agents.tools.enhance_inflatable_prompt", "refine_inflatable_prompt"),
    ("score_inflatable_prompt", "agents.tools.enhance_inflatable_prompt", "score_inflatable_prompt"),
    ("check_inflatable_image", "agents.tools.enhance_inflatable_prompt", "check_inflatable_image"),
]


def get_required_system_tools() -> List[tuple]:
    """Return list of (tool_id, module_path, function_name) for system tools."""
    return REQUIRED_SYSTEM_TOOLS


class ToolLoader:
    """Handles loading tools from config, DB, and other sources."""

    @staticmethod
    def load_required_system_tools() -> Dict[str, ToolInfo]:
        """Load mandatory system tools that are always available."""
        tools = {}
        for tool_id, module_path, func_name in REQUIRED_SYSTEM_TOOLS:
            try:
                module = __import__(module_path, fromlist=[func_name])
                func = getattr(module, func_name)
                tools[tool_id] = {
                    "provider": "system",
                    "tool_function": func,
                }
            except ImportError as e:
                logger.error("tool_register_failed", tool=tool_id, error=str(e))
        return tools

    @staticmethod
    def load_provider_tools(
        tool_mapping: Dict[str, ToolInfo]
    ) -> Dict[str, ToolInfo]:
        """Load tools based on configured providers."""
        tools = {}
        for provider_name, provider_config in config_service.app_config.items():
            api_key = provider_config.get("api_key", "")
            if not api_key:
                env_key = f"{provider_name.upper().replace('-', '_')}_API_KEY"
                api_key = os.getenv(env_key, "")

            if api_key:
                for tool_id, tool_info in tool_mapping.items():
                    if tool_info.get("provider") == provider_name:
                        tools[tool_id] = tool_info
        return tools

    @staticmethod
    async def load_comfyui_tools() -> Dict[str, ToolInfo]:
        """Load ComfyUI workflow tools from database."""
        tools = {}
        try:
            workflows = await db_service.list_comfy_workflows()
        except Exception as exc:
            logger.error("comfy_workflows_list_failed", error=str(exc))
            return tools

        for wf in workflows:
            try:
                from agents.tools.comfy_dynamic import sanitize_tool_name
                tool_fn = build_tool(wf)
                unique_name = f"comfyui_{sanitize_tool_name(wf['name'])}"
                tools[unique_name] = {
                    "provider": "comfyui",
                    "tool_function": tool_fn,
                    "display_name": wf["name"],
                    "type": "image",
                }
            except Exception as exc:
                logger.error("comfy_tool_create_failed", workflow_id=wf.get('id'), error=str(exc))

        return tools

    @staticmethod
    async def initialize(
        tool_mapping: Dict[str, ToolInfo],
        registry
    ) -> None:
        """Initialize registry with all available tools."""
        registry.clear()
        registry.tools.update(ToolLoader.load_required_system_tools())
        registry.tools.update(ToolLoader.load_provider_tools(tool_mapping))
        if config_service.app_config.get("comfyui", {}).get("url", ""):
            comfy_tools = await ToolLoader.load_comfyui_tools()
            registry.tools.update(comfy_tools)
