import os
import traceback
import asyncio
from typing import Optional, List, Any, Dict
from pydantic import BaseModel
from openai.types import Image
from .image_base_provider import ImageProviderBase
from ..utils.image_utils import get_image_info_and_save, generate_image_id
from services.config_service import FILES_DIR
from utils.http_client import HttpClient
from services.config_service import config_service
from services.log_service import tool_logger as logger


class JaazImagesResponse(BaseModel):
    """Image response class, Jaaz API return format, consistent with OpenAI"""
    created: int
    """The Unix timestamp (in seconds) of when the image was created."""

    data: Optional[List[Image]] = None
    """The list of generated images."""


class TaskSearchResponse(BaseModel):
    """Task search response model"""
    success: bool
    data: Dict[str, Any]


class JaazImageProvider(ImageProviderBase):
    """Jaaz Cloud image generation provider implementation"""

    def _build_url(self) -> str:
        """Build request URL"""
        config = config_service.app_config.get('jaaz', {})
        api_url = str(config.get("url", "")).rstrip("/")
        api_token = str(config.get("api_key", ""))

        if not api_url:
            raise ValueError("Jaaz API URL is not configured")
        if not api_token:
            raise ValueError("Jaaz API token is not configured")
        if api_url.rstrip('/').endswith('/api/v1'):
            return f"{api_url.rstrip('/')}/image/generations"
        else:
            return f"{api_url.rstrip('/')}/api/v1/image/generations"

    def _build_search_url(self) -> str:
        """Build task search URL"""
        config = config_service.app_config.get('jaaz', {})
        api_url = str(config.get("url", "")).rstrip("/")

        if api_url.rstrip('/').endswith('/api/v1'):
            return f"{api_url.rstrip('/')}/task/search"
        else:
            return f"{api_url.rstrip('/')}/api/v1/task/search"

    def _build_headers(self) -> Dict[str, str]:
        config = config_service.app_config.get('jaaz', {})
        api_token = str(config.get("api_key", ""))

        """Build request headers"""
        return {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json"
        }

    async def _search_cloud_task(self, prompt: str) -> Optional[Dict[str, Any]]:
        """
        Search for existing cloud task

        Args:
            prompt: The generation prompt

        Returns:
            Task data if found and succeeded, None otherwise
        """
        try:
            url = self._build_search_url()
            headers = self._build_headers()

            search_data = {
                "prompt": prompt,
                "type": 'image',
            }

            async with HttpClient.create_aiohttp() as session:
                async with session.post(url, headers=headers, json=search_data) as response:
                    if response.status != 200:
                        logger.error("task_search_failed", status=response.status)
                        return None

                    json_data = await response.json()
                    if json_data.get('success') and json_data.get('data', {}).get('found'):
                        task = json_data['data']['task']
                        logger.info("found_cloud_task", task_id=task.get("id"), status=task.get("status"))
                        return task

                    return None

        except Exception as e:
            logger.error("error_searching_cloud_task", error=str(e))
            return None

    async def _wait_for_task_completion(self, prompt: str, max_wait_time: int = 300) -> Optional[Dict[str, Any]]:
        """
        Wait for cloud task to complete

        Args:
            prompt: The generation prompt
            model: The model used
            max_wait_time: Maximum wait time in seconds

        Returns:
            Task data if succeeded, None otherwise
        """
        start_time = asyncio.get_event_loop().time()
        no_task_retry_count = 0
        max_no_task_retries = 5

        while True:
            task = await self._search_cloud_task(prompt)

            if not task:
                no_task_retry_count += 1
                if no_task_retry_count <= max_no_task_retries:
                    logger.debug("cloud_task_retry", count=no_task_retry_count, max=max_no_task_retries)
                    await asyncio.sleep(3)
                    continue
                else:
                    logger.warning("no_cloud_task_found_after_retries")
                    return None

            # Reset retry count when task is found
            no_task_retry_count = 0

            status = task.get('status')
            logger.info("cloud_task_status", status=status)

            if status == 'succeeded':
                logger.info("cloud_task_completed")
                return task
            elif status == 'failed':
                logger.error("cloud_task_failed")
                return None
            elif status == 'processing':
                # Check if we've exceeded max wait time
                elapsed = asyncio.get_event_loop().time() - start_time
                if elapsed > max_wait_time:
                    logger.warning("cloud_task_timeout", max_wait_time=max_wait_time)
                    return None

                logger.debug("cloud_task_processing")
                await asyncio.sleep(2)
            else:
                logger.warning("unknown_cloud_task_status", status=status)
                return None

    async def _process_cloud_task_result(self, task: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> tuple[str, int, int, str]:
        """
        Process cloud task result and download image

        Args:
            task: Task data from cloud
            metadata: Optional metadata

        Returns:
            tuple[str, int, int, str]: (mime_type, width, height, filename)
        """
        result_url = task.get('result_url')
        if not result_url:
            raise Exception('No result_url found in cloud task')

        logger.info("using_cloud_task_result", url=result_url)

        # Download and save the image from cloud result
        image_id = generate_image_id()
        mime_type, width, height, extension = await get_image_info_and_save(
            str(result_url),
            os.path.join(FILES_DIR, f'{image_id}'),
            metadata=metadata
        )

        filename = f'{image_id}.{extension}'
        return mime_type, width, height, filename

    async def _make_request(self, url: str, headers: Dict[str, str], data: Dict[str, Any]) -> JaazImagesResponse:
        """
        Send HTTP request and handle response

        Returns:
            JaazImagesResponse: Jaaz compatible image response object
        """
        async with HttpClient.create_aiohttp() as session:
            logger.debug("jaaz_api_request", url=url, model=data["model"], prompt=f"{data['prompt'][:50]}...")

            async with session.post(url, headers=headers, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    error_msg = f"HTTP {response.status}: {error_text}"
                    logger.error("jaaz_api_error", error=error_msg)
                    raise Exception(f'Image generation failed: {error_msg}')

                # Parse JSON data
                json_data = await response.json()
                logger.debug("jaaz_api_response", response=f"{str(json_data)[:200]}...")

                return JaazImagesResponse(**json_data)

    async def _process_response(
        self,
        res: JaazImagesResponse,
        error_prefix: str = "Jaaz",
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[str, int, int, str]:
        """
        Process ImagesResponse and save image

        Args:
            res: OpenAI ImagesResponse object
            error_prefix: Error message prefix

        Returns:
            tuple[str, int, int, str]: (mime_type, width, height, filename)
        """
        if res.data and len(res.data) > 0:
            image_data = res.data[0]
            if hasattr(image_data, 'url') and image_data.url:
                image_url = image_data.url
                image_id = generate_image_id()
                mime_type, width, height, extension = await get_image_info_and_save(
                    image_url,
                    os.path.join(FILES_DIR, f'{image_id}'),
                    metadata=metadata
                )

                filename = f'{image_id}.{extension}'
                return mime_type, width, height, filename

        # If no valid image data found
        raise Exception(
            f'{error_prefix} image generation failed: No valid image data in response')

    async def generate(
        self,
        prompt: str,
        model: str,
        aspect_ratio: str = "1:1",
        input_images: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> tuple[str, int, int, str]:
        """
        Generate image using Jaaz API service
        Supports both Replicate format and OpenAI format models

        Returns:
            tuple[str, int, int, str]: (mime_type, width, height, filename)
        """
        # Private deployment check: if using jaaz.cloud, generate placeholder
        config = config_service.app_config.get('jaaz', {})
        jaaz_url = config.get('url', '')
        if 'jaaz.app' in jaaz_url:
            try:
                return await self._generate_replicate_image(
                    prompt=prompt,
                    model=model,
                    aspect_ratio=aspect_ratio,
                    input_images=input_images,
                    metadata=metadata,
                    **kwargs
                )
            except Exception as e:
                if '402' in str(e) or 'Insufficient balance' in str(e):
                    logger.warning("jaaz_balance_insufficient")
                    return await self._generate_placeholder_image(prompt, metadata)
                raise e

        # Check if it's an OpenAI model
        if model.startswith('openai/'):
            return await self._generate_openai_image(
                prompt=prompt,
                model=model,
                input_images=input_images,
                aspect_ratio=aspect_ratio,
                metadata=metadata,
                **kwargs
            )

        # Replicate compatible logic
        return await self._generate_replicate_image(
            prompt=prompt,
            model=model,
            aspect_ratio=aspect_ratio,
            input_images=input_images,
            metadata=metadata,
            **kwargs
        )

    async def _generate_replicate_image(
        self,
        prompt: str,
        model: str,
        aspect_ratio: str = "1:1",
        input_images: Optional[list[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> tuple[str, int, int, str]:
        """Generate Replicate format image"""
        try:
            url = self._build_url()
            headers = self._build_headers()

            # Build request data, consistent with Replicate format
            data = {
                "prompt": prompt,
                "model": model,
                "aspect_ratio": aspect_ratio,
            }

            # Add input images if provided
            if input_images:
                # For Replicate format, we take the first image as input_image
                data['input_image'] = input_images[0]
                if len(input_images) > 1:
                    logger.warning("replicate_single_image_only", input_count=len(input_images))

            res = await self._make_request(url, headers, data)
            return await self._process_response(res, "Jaaz", metadata)

        except Exception as e:
            logger.error("error_generating_image_jaaz", error=str(e))
            traceback.print_exc()

            # Always attempt cloud task fallback on any error
            logger.info("attempting_cloud_task_fallback")
            try:
                task = await self._wait_for_task_completion(prompt)
                if task:
                    logger.info("recovered_using_cloud_task")
                    return await self._process_cloud_task_result(task, metadata)
                else:
                    logger.warning("no_cloud_task_for_recovery")
            except Exception as fallback_error:
                logger.error("cloud_task_fallback_failed", error=str(fallback_error))

            # If fallback fails, raise original error
            raise e

    async def _generate_placeholder_image(
        self,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> tuple[str, int, int, str]:
        from PIL import Image, ImageDraw, ImageFont
        import io
        import os

        width, height = 512, 512
        img = Image.new('RGB', (width, height), color=(40, 40, 50))
        draw = ImageDraw.Draw(img)

        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

        draw.text((width//2, height//3), "Jaaz Private Deployment", fill=(255, 255, 255), font=font_large, anchor="mm")
        draw.text((width//2, height//2), "Image generation requires", fill=(200, 200, 200), font=font_small, anchor="mm")
        draw.text((width//2, height//2 + 30), "ComfyUI workflow setup", fill=(200, 200, 200), font=font_small, anchor="mm")
        draw.text((width//2, height//2 + 60), f"Prompt: {prompt[:50]}...", fill=(150, 150, 150), font=font_small, anchor="mm")

        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)

        image_id = generate_image_id()
        save_path = os.path.join(FILES_DIR, f'{image_id}.png')
        with open(save_path, 'wb') as f:
            f.write(buffer.getvalue())

        return 'image/png', width, height, f'{image_id}.png'

    async def _generate_openai_image(
        self,
        prompt: str,
        model: str,
        input_images: Optional[list[str]] = None,
        aspect_ratio: str = "1:1",
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> tuple[str, int, int, str]:
        """
        Generate image using Jaaz API service calling OpenAI model
        Compatible with OpenAI image generation API

        Returns:
            tuple[str, int, int, str]: (mime_type, width, height, filename)
        """
        try:
            url = self._build_url()
            headers = self._build_headers()

            # Build request data
            enhanced_prompt = f"{prompt} Aspect ratio: {aspect_ratio}"

            data = {
                "model": model,
                "prompt": enhanced_prompt,
                "n": kwargs.get("num_images", 1),
                "size": 'auto',
                "mask": None,  # Add mask here if needed
            }

            # Add input images if provided
            if input_images:
                data["input_images"] = input_images
                logger.info("using_input_images", count=len(input_images))

            res = await self._make_request(url, headers, data)
            return await self._process_response(res, "Jaaz OpenAI", metadata)

        except Exception as e:
            logger.error("error_generating_image_jaaz_openai", error=str(e))
            traceback.print_exc()

            # Always attempt cloud task fallback on any error
            logger.info("attempting_cloud_task_fallback")
            try:
                # For OpenAI models, use the original prompt
                enhanced_prompt = f"{prompt} Aspect ratio: {aspect_ratio}"
                task = await self._wait_for_task_completion(enhanced_prompt)
                if task:
                    logger.info("recovered_using_cloud_task")
                    return await self._process_cloud_task_result(task, metadata)
                else:
                    logger.warning("no_cloud_task_for_recovery")
            except Exception as fallback_error:
                logger.error("cloud_task_fallback_failed", error=str(fallback_error))

            # If fallback fails, raise original error
            raise e
