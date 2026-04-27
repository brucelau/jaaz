from pathlib import Path
from typing import List
from models.tool_model import ToolInfoJson
from .base_config import BaseAgentConfig, HandoffConfig


class PneumatEnhancerAgentConfig(BaseAgentConfig):
    def __init__(self, tool_list: List[ToolInfoJson]) -> None:
        prompts_dir = Path(__file__).parent.parent.parent.parent / "config" / "prompts"
        system_prompt_path = prompts_dir / "enhancer_system_prompt.md"
        system_prompt = system_prompt_path.read_text()

        handoffs: List[HandoffConfig] = [
            {
                'agent_name': 'image_video_creator',
                'description': 'Transfer to image_video_creator after air-mold prompt enhancement is complete. Include the English prompt in the transfer message.'
            }
        ]

        super().__init__(
            name='pneumat_enhancer',
            tools=tool_list,
            system_prompt=system_prompt,
            handoffs=handoffs
        )