import os
import traceback
import asyncio
import requests
import hashlib
from typing import Optional, Any, Tuple
from .image_base_provider import ImageProviderBase
from ..utils.image_utils import get_image_info_and_save, generate_image_id
from services.config_service import FILES_DIR, config_service


class IdeogramProvider(ImageProviderBase):
    """Ideogram image generation provider implementation"""

    def __init__(self):
        self.api_url = "https://api.ideogram.ai/v1/ideogram-v3/generate"
        self.max_retries = 3
        self.retry_delay = 2

    async def generate(
        self,
        prompt: str,
        model: str,
        aspect_ratio: str = "1:1",
        input_images: Optional[list[str]] = None,
        **kwargs: Any
    ) -> Tuple[str, int, int, str]:
        """
        Generate image using Ideogram API

        Returns:
            Tuple[str, int, int, str]: (mime_type, width, height, filename)
        """

        config = config_service.app_config.get('ideogram', {})
        self.api_key = str(config.get("api_key", ""))

        if not self.api_key:
            self.api_key = os.getenv("IDEOGRAM_API_KEY", "")
        if not self.api_key:
            self.api_key = os.getenv("IDEOGRAM_KEY", "")
        if not self.api_key:
            raise ValueError("Ideogram API key is not configured")

        def _call_api():
            data = {
                "prompt": prompt,
                "aspect_ratio": self._map_aspect_ratio(aspect_ratio),
                "style_type": "REALISTIC",
                "model": "V_2"
            }
            headers = {"Api-Key": self.api_key}

            response = requests.post(self.api_url, headers=headers, json=data, timeout=120)

            if response.status_code == 200:
                result = response.json()
                if "data" in result and len(result["data"]) > 0:
                    image_url = result["data"][0].get("url")
                    image_id = generate_image_id()
                    mime_type, width, height, extension = asyncio.run(
                        get_image_info_and_save(image_url, os.path.join(FILES_DIR, f'{image_id}'))
                    )
                    return mime_type, width, height, f'{image_id}.{extension}'

            if response.status_code == 429:
                raise Exception("Ideogram rate limit exceeded")

            raise Exception(f"Ideogram API error: HTTP {response.status_code}: {response.text[:200]}")

        try:
            mime_type, width, height, filename = await asyncio.to_thread(_call_api)
            return mime_type, width, height, filename
        except Exception as e:
            print('Error generating image with Ideogram:', e)
            traceback.print_exc()
            raise e

    def _map_aspect_ratio(self, aspect_ratio: str) -> str:
        """Map standard aspect ratio to Ideogram format"""
        mapping = {
            "1:1": "1x1",
            "16:9": "16x9",
            "4:3": "4x3",
            "3:4": "3x4",
            "9:16": "9x16"
        }
        return mapping.get(aspect_ratio, "1x1")