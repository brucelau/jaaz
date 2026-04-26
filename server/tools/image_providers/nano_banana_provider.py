import os
import traceback
import asyncio
import requests
import base64
from PIL import Image
import io
from typing import Optional, Any, Tuple
from .image_base_provider import ImageProviderBase
from ..utils.image_utils import generate_image_id
from services.config_service import FILES_DIR, config_service
from services.log_service import tool_logger as logger


class NanoBananaProvider(ImageProviderBase):
    """Nano Banana (Gemini Flash Image) provider implementation"""

    def __init__(self):
        self.model = "gemini-3.1-flash-image-preview"
        self.api_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    async def generate(
        self,
        prompt: str,
        model: str,
        aspect_ratio: str = "1:1",
        input_images: Optional[list[str]] = None,
        **kwargs: Any
    ) -> Tuple[str, int, int, str]:
        """
        Generate image using Nano Banana (Gemini Flash Image) API

        Returns:
            Tuple[str, int, int, str]: (mime_type, width, height, filename)
        """

        config = config_service.app_config.get('nano_banana', {})
        self.api_key = str(config.get("api_key", ""))

        if not self.api_key:
            self.api_key = os.getenv("NANO_BANANA_API_KEY", "")
            if not self.api_key:
                self.api_key = os.getenv("GEMINI_API_KEY", "")
            if not self.api_key:
                raise ValueError("Nano Banana API key is not configured")

        def _call_api():
            url = f"{self.api_url}?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.9, "topP": 1, "maxOutputTokens": 2048}
            }

            max_retries = 3
            last_error = None

            for attempt in range(max_retries):
                try:
                    response = requests.post(
                        url,
                        headers={"Content-Type": "application/json"},
                        json=payload,
                        timeout=180
                    )

                    if response.status_code == 200:
                        result = response.json()

                        for part in result.get("candidates", [{}])[0].get("content", {}).get("parts", []):
                            if "inlineData" in part:
                                img_data = base64.b64decode(part["inlineData"]["data"])
                                image_id = generate_image_id()
                                image_path = os.path.join(FILES_DIR, f'{image_id}.png')

                                img = Image.open(io.BytesIO(img_data))
                                width, height = img.size
                                img.save(image_path, quality=95)

                                return "image/png", width, height, f'{image_id}.png'

                        raise Exception("No image in Nano Banana response")

                    last_error = f"HTTP {response.status_code}: {response.text[:200]}"
                except requests.exceptions.Timeout:
                    last_error = f"Timeout on attempt {attempt + 1}"
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(5)
                    continue
                except Exception as e:
                    last_error = str(e)
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2)
                    continue

            raise Exception(f"Nano Banana API error after {max_retries} retries: {last_error}")

        try:
            mime_type, width, height, filename = await asyncio.to_thread(_call_api)
            return mime_type, width, height, filename
        except Exception as e:
            logger.error("error_generating_image_nano_banana", error=str(e))
            traceback.print_exc()
            raise e