from typing import Optional, List, Dict
from pathlib import Path
from dataclasses import dataclass
import os
import toml
import httpx
from web.services.log_service import tool_logger as logger


@dataclass
class EnhancementResult:
    original_input: str
    matched_patterns: List
    filtered_patterns: List
    enhanced_prompt: str


class PromptEnhancer:
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    DEFAULT_TEMPLATE_PATH = Path(__file__).parent.parent.parent.parent / "config" / "prompts" / "enhancer_template.md"
    CONFIG_PATH = Path(__file__).parent.parent.parent.parent / "config" / "config.toml"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or self._load_api_key()
        self._max_tokens = self._load_max_tokens()
        self._template = self._load_template()

    def _load_api_key(self) -> str:
        try:
            if self.CONFIG_PATH.exists():
                config = toml.load(self.CONFIG_PATH)
                return config.get("nano_banana", {}).get("api_key", "") or config.get("gemini", {}).get("api_key", "")
        except Exception as e:
            logger.warning("config_load_error", error=str(e))
        return ""

    def _load_max_tokens(self) -> int:
        try:
            if self.CONFIG_PATH.exists():
                config = toml.load(self.CONFIG_PATH)
                return config.get("gemini", {}).get("enhancer_max_tokens", 8192)
        except Exception as e:
            logger.warning("config_load_error", error=str(e))
        return 8192

    def _load_template(self) -> str:
        try:
            if self.DEFAULT_TEMPLATE_PATH.exists():
                return self.DEFAULT_TEMPLATE_PATH.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning("template_load_error", path=str(self.DEFAULT_TEMPLATE_PATH), error=str(e))
        return ""

    def get_template(self) -> str:
        return self._template

    async def enhance(self, user_input: str, feedback: Optional[List[str]] = None) -> EnhancementResult:
        logger.info("enhancer_template_loaded",
            template_length=len(self._template),
            template_preview=self._template[:200]
        )

        enhanced = await self._enhance_with_llm(user_input, feedback)

        logger.info("enhancer_result",
            original_input=user_input,
            enhanced_prompt=enhanced
        )

        return EnhancementResult(
            original_input=user_input,
            matched_patterns=[],
            filtered_patterns=[],
            enhanced_prompt=enhanced,
        )

    async def _enhance_with_llm(
        self,
        user_input: str,
        feedback: Optional[List[str]] = None,
    ) -> str:
        feedback_note = ""
        if feedback:
            feedback_note = "\n".join(f"- {f}" for f in feedback)
            feedback_note = f"\n【改进要求】请解决以下问题：\n{feedback_note}\n"

        prompt = self._template.format(
            user_input=user_input,
            feedback_note=feedback_note
        )

        api_key = self.api_key
        if not api_key:
            return user_input

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.GEMINI_MODEL}:generateContent?key={api_key}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": self._max_tokens}
        }

        logger.info("gemini_enhancer_request",
            user_input=user_input,
            prompt_to_gemini=prompt,
            temperature=0.7,
            max_tokens=self._max_tokens
        )

        max_retries = 3
        for attempt in range(max_retries):
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, json=payload)

            logger.info("gemini_status", attempt=attempt + 1, status=response.status_code, body=response.text[:300])

            if response.status_code == 200:
                data = response.json()
                result = data["candidates"][0]["content"]["parts"][0]["text"]
                logger.info("gemini_enhancer_response", full_response=result)
                return result.strip()

            if response.status_code == 503 and attempt < max_retries - 1:
                import asyncio
                wait_time = (attempt + 1) * 2
                logger.info("gemini_503_retry", attempt=attempt + 1, wait_seconds=wait_time)
                await asyncio.sleep(wait_time)
                continue

            break

        return user_input
