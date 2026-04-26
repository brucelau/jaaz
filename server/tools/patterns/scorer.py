from dataclasses import dataclass
from typing import List, Dict, Optional
from pathlib import Path
import re
import os
import json
from services.log_service import tool_logger as logger


@dataclass
class AirMoldScore:
    material_accuracy: float
    structural_soundness: float
    visual_quality: float
    color_accuracy: float
    overall: float

    def to_dict(self) -> Dict:
        return {
            "material_accuracy": self.material_accuracy,
            "structural_soundness": self.structural_soundness,
            "visual_quality": self.visual_quality,
            "color_accuracy": self.color_accuracy,
            "overall": self.overall,
        }


class AirMoldScorer:
    PASS_THRESHOLD = float(os.getenv("PASS_THRESHOLD", "3.5"))
    SELENE_URL = os.getenv("SELENE_URL", "http://100.75.202.111:8080/v1/chat/completions")
    SELENE_TIMEOUT = int(os.getenv("SELENE_TIMEOUT", "180"))

    DEFAULT_TEMPLATE_PATH = Path(__file__).parent.parent.parent / "config" / "prompts" / "scorer_template.md"

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

    def evaluate_with_feedback(
        self,
        prompt: str,
        feedback: Optional[List[str]] = None
    ) -> Dict:
        feedback_note = ""
        if feedback:
            feedback_note = "\n".join(f"- {f}" for f in feedback)
            feedback_note = f"\n参考之前的问题：\n{feedback_note}\n"

        eval_prompt = self._template.format(
            prompt=prompt,
            feedback_note=feedback_note
        )

        try:
            import requests
            logger.info("selene_scoring", prompt=f"{prompt[:80]}...")
            resp = requests.post(
                self.SELENE_URL,
                json={
                    "messages": [{"role": "user", "content": eval_prompt}],
                    "max_tokens": 500,
                    "temperature": 0.3
                },
                timeout=self.SELENE_TIMEOUT
            )
            if resp.status_code == 200:
                result_text = resp.json()["choices"][0]["message"]["content"]
                logger.info("selene_response", response=f"{result_text[:200]}...")
                return self._parse_selene_response(result_text, prompt)
        except Exception as e:
            logger.error("selene_error", error=str(e))

        return {
            "score": {
                "material_accuracy": 0,
                "inflatable_structure": 0,
                "festival_theme": 0,
                "style": 0,
                "main_shape": 0,
                "product_elements": 0,
                "usage_scene": 0,
                "time_setting": 0,
                "lighting_effect": 0,
                "atmosphere": 0,
                "background": 0,
                "composition": 0,
                "visual_quality": 0,
                "color_accuracy": 0,
                "overall": 0
            },
            "suggestions": ["评分服务暂时不可用"],
            "pass": False
        }

    def _parse_selene_response(self, response_text: str, prompt: str) -> Dict:
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                material = float(data.get("material_accuracy", 0))
                inflatable = float(data.get("inflatable_structure", 0))
                festival = float(data.get("festival_theme", 0))
                style = float(data.get("style", 0))
                main_shape = float(data.get("main_shape", 0))
                product_elements = float(data.get("product_elements", 0))
                usage_scene = float(data.get("usage_scene", 0))
                time_setting = float(data.get("time_setting", 0))
                lighting = float(data.get("lighting_effect", 0))
                atmosphere = float(data.get("atmosphere", 0))
                background = float(data.get("background", 0))
                composition = float(data.get("composition", 0))
                visual = float(data.get("visual_quality", 0))
                color = float(data.get("color_accuracy", 0))

                scores = [material, inflatable, festival, style, main_shape,
                         product_elements, usage_scene, time_setting, lighting,
                         atmosphere, background, composition, visual, color]
                overall = sum(scores) / len(scores) if scores else 0

                feedback = data.get("feedback", "")
                passed = data.get("pass", overall >= self.PASS_THRESHOLD)

                return {
                    "score": {
                        "material_accuracy": round(material, 2),
                        "inflatable_structure": round(inflatable, 2),
                        "festival_theme": round(festival, 2),
                        "style": round(style, 2),
                        "main_shape": round(main_shape, 2),
                        "product_elements": round(product_elements, 2),
                        "usage_scene": round(usage_scene, 2),
                        "time_setting": round(time_setting, 2),
                        "lighting_effect": round(lighting, 2),
                        "atmosphere": round(atmosphere, 2),
                        "background": round(background, 2),
                        "composition": round(composition, 2),
                        "visual_quality": round(visual, 2),
                        "color_accuracy": round(color, 2),
                        "overall": round(overall, 2)
                    },
                    "suggestions": [feedback] if feedback else [],
                    "pass": passed
                }
        except Exception as e:
            logger.error("parse_error", error=str(e))

        return {
            "score": {
                "material_accuracy": 0,
                "inflatable_structure": 0,
                "festival_theme": 0,
                "style": 0,
                "main_shape": 0,
                "product_elements": 0,
                "usage_scene": 0,
                "time_setting": 0,
                "lighting_effect": 0,
                "atmosphere": 0,
                "background": 0,
                "composition": 0,
                "visual_quality": 0,
                "color_accuracy": 0,
                "overall": 0
            },
            "suggestions": ["评分解析失败"],
            "pass": False
        }


_scorer: Optional[AirMoldScorer] = None


def get_scorer() -> AirMoldScorer:
    global _scorer
    if _scorer is None:
        _scorer = AirMoldScorer()
    return _scorer
