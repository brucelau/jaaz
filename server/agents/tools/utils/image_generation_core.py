"""
Image generation core module
Contains the main orchestration logic for image generation across different providers
"""

from typing import Optional, Dict, Any
from web.services.config_service import DEFAULT_PORT
from agents.tools.utils.image_utils import process_input_image
from ..image_providers.image_base_provider import ImageProviderBase
from web.services.log_service import tool_logger as logger

# 导入所有提供商以确保自动注册 (不要删除这些导入)
from ..image_providers.jaaz_provider import JaazImageProvider
from ..image_providers.openai_provider import OpenAIImageProvider
from ..image_providers.replicate_provider import ReplicateImageProvider
from ..image_providers.volces_provider import VolcesProvider
from ..image_providers.wavespeed_provider import WavespeedProvider
from ..image_providers.ideogram_provider import IdeogramProvider
from ..image_providers.nano_banana_provider import NanoBananaProvider

# from ..image_providers.comfyui_provider import ComfyUIProvider
from .image_canvas_utils import (
    save_image_to_canvas,
)
import time

IMAGE_PROVIDERS: dict[str, ImageProviderBase] = {
    # "jaaz": JaazImageProvider(),  # disabled - no longer using jaaz cloud API
    "openai": OpenAIImageProvider(),
    "replicate": ReplicateImageProvider(),
    "volces": VolcesProvider(),
    "wavespeed": WavespeedProvider(),
    "ideogram": IdeogramProvider(),
    "nano_banana": NanoBananaProvider(),
}


from web.websocket.emitter import send_to_websocket, broadcast_session_update

async def generate_image_with_provider(
    canvas_id: str,
    session_id: str,
    provider: str,
    model: str,
    # image generator args
    prompt: str,
    aspect_ratio: str = "1:1",
    input_images: Optional[list[str]] = None,
) -> str:
    logger.info("image_generation_start", provider=provider, model=model, aspect_ratio=aspect_ratio, prompt=prompt[:100])
    
    if session_id:
        await send_to_websocket(session_id, {
            "type": "info",
            "message": f"正在使用 {provider} 生成图像..."
        })
    provider_instance = IMAGE_PROVIDERS.get(provider)
    if not provider_instance:
        raise ValueError(f"Unknown provider: {provider}")

    # Process input images for the provider
    processed_input_images: list[str] | None = None
    if input_images:
        processed_input_images = []
        for image_path in input_images:
            processed_image = await process_input_image(image_path)
            if processed_image:
                processed_input_images.append(processed_image)

        logger.debug("using_input_images", count=len(processed_input_images))

    # Prepare metadata with all generation parameters
    metadata: Dict[str, Any] = {
        "prompt": prompt,
        "model": model,
        "provider": provider,
        "aspect_ratio": aspect_ratio,
        "input_images": input_images or [],
    }

    # Generate image using the selected provider
    mime_type, width, height, filename = await provider_instance.generate(
        prompt=prompt,
        model=model,
        aspect_ratio=aspect_ratio,
        input_images=processed_input_images,
        metadata=metadata,
    )

    # Save image to canvas
    image_url = await save_image_to_canvas(
        session_id, canvas_id, filename, mime_type, width, height
    )

    return f"image generated successfully ![image_id: {filename}](http://localhost:{DEFAULT_PORT}{image_url})"
