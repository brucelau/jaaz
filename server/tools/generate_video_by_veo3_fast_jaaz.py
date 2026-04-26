from typing import Annotated
from pydantic import BaseModel, Field
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.runnables import RunnableConfig
from services.jaaz_service import JaazService
from tools.video_generation.video_canvas_utils import send_video_start_notification, process_video_result
from services.tool_confirmation_manager import tool_confirmation_manager
from ws_manager.emitter import send_to_websocket
from services.log_service import tool_logger as logger
import json

class GenerateVideoByVeo3FastInputSchema(BaseModel):
    prompt: str = Field(
        description="Required. The prompt for video generation. Describe what you want to see in the video."
    )
    tool_call_id: Annotated[str, InjectedToolCallId]


@tool("generate_video_by_veo3_fast_jaaz",
      description="Generate high-quality videos using Veo3 Fast model. Fast text-to-video generation with optimized performance.",
      args_schema=GenerateVideoByVeo3FastInputSchema)
async def generate_video_by_veo3_fast_jaaz(
    prompt: str,
    config: RunnableConfig,
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> str:
    """
    Generate a video using Veo3 Fast model via Jaaz service
    """
    ctx = config.get('configurable', {})
    canvas_id = ctx.get('canvas_id', '')
    session_id = ctx.get('session_id', '')
    logger.info("veo3_start", tool_call_id=tool_call_id, canvas_id=canvas_id, session_id=session_id)

        # 检查是否需要确认
    arguments = {
        'prompt': prompt,
    }

    # 发送确认请求
    await send_to_websocket(session_id, {
        'type': 'tool_call_pending_confirmation',
        'id': tool_call_id,
        'name': 'generate_video_by_veo3_fast_jaaz',
        'arguments': json.dumps(arguments)
    })

    # 等待确认
    confirmed = await tool_confirmation_manager.request_confirmation(
        tool_call_id, session_id, 'generate_video_by_veo3_fast_jaaz', arguments
    )

    if not confirmed:
        return "Video generation cancelled by user."

    # Inject the tool call id into the context
    ctx['tool_call_id'] = tool_call_id

    try:
        # Send start notification
        await send_video_start_notification(
            session_id,
            f"Starting Veo3 Fast video generation..."
        )

        # Create Jaaz service and generate video
        jaaz_service = JaazService()
        result = await jaaz_service.generate_video(
            prompt=prompt,
            model="veo3-fast",
        )

        video_url = result.get('result_url')
        if not video_url:
            raise Exception("No video URL returned from generation")

        # Process video result (save, update canvas, notify)
        return await process_video_result(
            video_url=video_url,
            session_id=session_id,
            canvas_id=canvas_id,
            provider_name="jaaz_veo3_fast",
        )

    except Exception as e:
        logger.error("veo3_error", error=str(e))
        raise e


# Export the tool for easy import
__all__ = ["generate_video_by_veo3_fast_jaaz"]
