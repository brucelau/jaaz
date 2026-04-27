from typing import List, Optional, Dict
from pathlib import Path
import re
import os
import json
import httpx
from pydantic import BaseModel, Field, field_validator
from web.services.log_service import tool_logger as logger


class SeleneResponse(BaseModel):
    material_accuracy: float = 0.0
    inflatable_structure: float = 0.0
    festival_theme: float = 0.0
    style: float = 0.0
    main_shape: float = 0.0
    product_elements: float = 0.0
    usage_scene: float = 0.0
    time_setting: float = 0.0
    lighting_effect: float = 0.0
    atmosphere: float = 0.0
    background: float = 0.0
    composition: float = 0.0
    visual_quality: float = 0.0
    color_accuracy: float = 0.0
    inflatable_manufacturing: float = 0.0
    overall: float = 0.0
    passed: bool = Field(default=False, alias='pass')
    feedback: str = ""

    model_config = {
        'populate_by_name': True,
        'strict': False,
    }

    @field_validator('feedback', mode='before')
    @classmethod
    def coerce_feedback(cls, v):
        if v is None:
            return ""
        return str(v)

    @field_validator('passed', mode='before')
    @classmethod
    def coerce_passed(cls, v):
        if isinstance(v, bool):
            return v
        if isinstance(v, (int, float)):
            return bool(v)
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes')
        return False

    def to_score_dict(self) -> Dict[str, float]:
        return {
            "material_accuracy": round(self.material_accuracy, 2),
            "inflatable_structure": round(self.inflatable_structure, 2),
            "festival_theme": round(self.festival_theme, 2),
            "style": round(self.style, 2),
            "main_shape": round(self.main_shape, 2),
            "product_elements": round(self.product_elements, 2),
            "usage_scene": round(self.usage_scene, 2),
            "time_setting": round(self.time_setting, 2),
            "lighting_effect": round(self.lighting_effect, 2),
            "atmosphere": round(self.atmosphere, 2),
            "background": round(self.background, 2),
            "composition": round(self.composition, 2),
            "visual_quality": round(self.visual_quality, 2),
            "color_accuracy": round(self.color_accuracy, 2),
            "inflatable_manufacturing": round(self.inflatable_manufacturing, 2),
            "overall": round(self.overall, 2),
        }


class AirMoldScorer:
    PASS_THRESHOLD = float(os.getenv("PASS_THRESHOLD", "3.5"))
    SELENE_URL = os.getenv("SELENE_URL", "http://100.75.202.111:11434/v1/chat/completions")
    SELENE_TIMEOUT = int(os.getenv("SELENE_TIMEOUT", "180"))
    DEFAULT_TEMPLATE_PATH = Path(__file__).parent.parent.parent.parent / "config" / "prompts" / "scorer_template.md"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self._template = self._load_template()

    def _load_template(self) -> str:
        try:
            if self.DEFAULT_TEMPLATE_PATH.exists():
                return self.DEFAULT_TEMPLATE_PATH.read_text(encoding="utf-8")
        except Exception:
            pass
        return ""

    def get_template(self) -> str:
        return self._template

    def _extract_json(self, text: str) -> Optional[str]:
        text = text.strip()
        if text.startswith('```'):
            lines = text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            text = '\n'.join(lines)
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return match.group()
        try:
            json.loads(text)
            return text
        except json.JSONDecodeError:
            pass
        return None

    async def evaluate_with_feedback(
        self,
        prompt: str,
        feedback: Optional[List[str]] = None
    ) -> Dict:
        logger.info("selene_evaluate_called", prompt_length=len(prompt), feedback=feedback)
        feedback_note = ""
        if feedback:
            feedback_note = "\n".join(f"- {f}" for f in feedback)
            feedback_note = f"\n参考之前的问题：\n{feedback_note}\n"

        eval_prompt = self._template.replace("{prompt}", prompt).replace("{feedback_note}", feedback_note)

        try:
            logger.info("selene_scoring", prompt=f"{prompt[:80]}...")
            async with httpx.AsyncClient(timeout=float(self.SELENE_TIMEOUT)) as client:
                resp = await client.post(
                    self.SELENE_URL,
                    json={
                        "model": "selene",
                        "messages": [{"role": "user", "content": eval_prompt}],
                        "max_tokens": 500,
                        "temperature": 0.3
                    }
                )
            logger.info("selene_http_status", status=resp.status_code, body=resp.text[:300])
            if resp.status_code == 200:
                result_text = resp.json()["choices"][0]["message"]["content"]
                logger.info("selene_response", response=f"{result_text[:300]}...")
                parsed = self._parse_response(result_text)
                if parsed:
                    score_dict = parsed.to_score_dict()
                    scores = [v for k, v in score_dict.items() if k != 'overall']
                    overall = sum(scores) / len(scores) if scores else 0.0
                    passed = parsed.passed or overall >= self.PASS_THRESHOLD
                    return {
                        "score": score_dict,
                        "suggestions": [parsed.feedback] if parsed.feedback else [],
                        "pass": passed
                    }
            return {"score": {}, "suggestions": [], "pass": True, "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            logger.error("selene_error", error=str(e), type=type(e).__name__)

        return {
            "score": {
                "material_accuracy": 0, "inflatable_structure": 0, "festival_theme": 0,
                "style": 0, "main_shape": 0, "product_elements": 0, "usage_scene": 0,
                "time_setting": 0, "lighting_effect": 0, "atmosphere": 0, "background": 0,
                "composition": 0, "visual_quality": 0, "color_accuracy": 0,
                "inflatable_manufacturing": 0, "overall": 0
            },
            "suggestions": [],
            "pass": True,
            "error": "Selene unavailable"
        }

    def _parse_response(self, response_text: str) -> Optional[SeleneResponse]:
        json_str = self._extract_json(response_text)
        if not json_str:
            logger.error("parse_failed", reason="no json found", text=response_text[:200])
            return None
        try:
            data = json.loads(json_str)
            return SeleneResponse(**data)
        except Exception as e:
            logger.error("parse_error", error=str(e), text=json_str[:200])
            return None


_scorer: Optional[AirMoldScorer] = None


def get_scorer() -> AirMoldScorer:
    global _scorer
    if _scorer is None:
        _scorer = AirMoldScorer()
    return _scorer
