from pathlib import Path
from typing import List
from .base_config import BaseAgentConfig, HandoffConfig


class PlannerAgentConfig(BaseAgentConfig):
    """规划智能体 - 负责制定执行计划
    """

    def __init__(self) -> None:
        prompts_dir = Path(__file__).parent.parent.parent.parent / "config" / "prompts"
        system_prompt_path = prompts_dir / "planner_system_prompt.md"
        system_prompt = system_prompt_path.read_text()

        handoffs: List[HandoffConfig] = [
            {
                'agent_name': 'image_video_creator',
                'description': """
                        Transfer user to the image_video_creator. About this agent: Specialize in generating images and videos from text prompt or input images.
                        """
            },
            {
                'agent_name': 'pneumat_enhancer',
                'description': """
                        Transfer user to the pneumat_enhancer for air-mold/inflatable product design requests.
                        This agent will handle prompt enhancement with LLM scoring and automatically transfer to image generation.
                        Use this for: 气模、充气拱门、充气装饰、inflatable air-mold products.
                        """
            }
        ]

        super().__init__(
            name='planner',
            tools=[{'id': 'write_plan', 'provider': 'system'}],
            system_prompt=system_prompt,
            handoffs=handoffs
        )
