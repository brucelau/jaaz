from pathlib import Path
from typing import List

from models.tool_model import ToolInfoJson
from .base_config import BaseAgentConfig, HandoffConfig


PROMPTS_DIR = Path(__file__).parent.parent.parent.parent / "config" / "prompts"


def _load(name: str) -> str:
    return (PROMPTS_DIR / name).read_text()


class ImageVideoCreatorAgentConfig(BaseAgentConfig):
    def __init__(self, tool_list: List[ToolInfoJson]) -> None:
        handoffs: List[HandoffConfig] = []

        full_system_prompt = (
            _load("creator_handoff_reception.md") +
            _load("creator_system_prompt.md") +
            _load("creator_image_input_detection.md") +
            _load("creator_batch_generation.md") +
            _load("creator_error_handling.md")
        )

        super().__init__(
            name='image_video_creator',
            tools=tool_list,
            system_prompt=full_system_prompt,
            handoffs=handoffs
        )