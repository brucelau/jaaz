from typing import Annotated
from pydantic import BaseModel, Field
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.runnables import RunnableConfig
from tools.utils.image_generation_core import generate_image_with_provider


class GenerateImageByNanoBananaInputSchema(BaseModel):
    prompt: str = Field(
        description="Required. The prompt for image generation."
    )
    aspect_ratio: str = Field(
        description="Required. Aspect ratio of the image, only these values are allowed: 1:1, 16:9, 4:3, 3:4, 9:16. Choose the best fitting aspect ratio according to the prompt."
    )
    tool_call_id: Annotated[str, InjectedToolCallId]


@tool("generate_image_by_nano_banana",
      description="Generate an image by Nano Banana (Gemini Flash Image) model. Fast generation with good quality. This model does NOT support input images for reference or editing.",
      args_schema=GenerateImageByNanoBananaInputSchema)
async def generate_image_by_nano_banana(
    prompt: str,
    aspect_ratio: str,
    config: RunnableConfig,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    ctx = config.get('configurable', {})
    canvas_id = ctx.get('canvas_id', '')
    session_id = ctx.get('session_id', '')

    return await generate_image_with_provider(
        canvas_id=canvas_id,
        session_id=session_id,
        provider='nano_banana',
        prompt=prompt,
        aspect_ratio=aspect_ratio,
        model="gemini-3.1-flash-image-preview",
        input_images=None,
    )


__all__ = ["generate_image_by_nano_banana"]