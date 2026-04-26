from dataclasses import dataclass
from typing import List, Dict, Optional
import re
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
    MATERIAL_KEYWORDS = [
        "PVC", "TPU", "Dacron", "涤纶", "尼龙", "网布",
        "光滑", "防水", "耐磨", "加厚", "高弹性", "柔滑",
        "面料", "材质", "质感", "表面"
    ]

    STRUCTURE_KEYWORDS = [
        "充气", "接缝", "底座", "风机", "固定", "支撑",
        "立体", "比例", "对称", "稳固", "加固", "多点",
        "结构", "设计", "造型"
    ]

    VISUAL_KEYWORDS = [
        "构图", "光影", "照明", "阴影", "视角", "景深",
        "背景", "分辨率", "8K", "4K", "专业", "摄影"
    ]

    COLOR_KEYWORDS = [
        "红色", "蓝色", "绿色", "黄色", "紫色", "橙色",
        "粉色", "白色", "黑色", "灰色", "金色", "银色",
        "配色", "色系", "Pantone", "色彩", "颜色", "色调"
    ]

    PASS_THRESHOLD = 3.5
    SELENE_URL = "http://100.75.202.111:8080/v1/chat/completions"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def score_prompt(self, prompt: str) -> AirMoldScore:
        material_score = self._score_dimension(prompt, self.MATERIAL_KEYWORDS)
        structure_score = self._score_dimension(prompt, self.STRUCTURE_KEYWORDS)
        visual_score = self._score_dimension(prompt, self.VISUAL_KEYWORDS)
        color_score = self._score_dimension(prompt, self.COLOR_KEYWORDS)

        overall = (material_score + structure_score + visual_score + color_score) / 4

        return AirMoldScore(
            material_accuracy=material_score,
            structural_soundness=structure_score,
            visual_quality=visual_score,
            color_accuracy=color_score,
            overall=overall
        )

    def score_batch(self, prompts: List[str]) -> List[AirMoldScore]:
        return [self.score_prompt(p) for p in prompts]

    def evaluate_batch(self, prompts: List[str]) -> List[Dict]:
        return [self.evaluate_and_suggest(p) for p in prompts]

    def _score_dimension(self, prompt: str, keywords: List[str]) -> float:
        prompt_lower = prompt.lower()
        matched = sum(1 for kw in keywords if kw.lower() in prompt_lower)
        base_score = min(matched / 3.0 * 5, 5.0)
        return round(base_score, 2)

    def evaluate_and_suggest(
        self,
        prompt: str,
        api_key: Optional[str] = None
    ) -> Dict:
        score = self.score_prompt(prompt)
        suggestions = []

        if score.material_accuracy < 3:
            suggestions.append("材质不够明确，缺少 PVC/TPU/防水面料 等专业材质描述")
        if score.structural_soundness < 3:
            suggestions.append("结构描述不足，需强化 充气设计/接缝加固/底座支撑 等要点")
        if score.visual_quality < 3:
            suggestions.append("视觉效果待提升，缺乏 专业摄影/8K分辨率/光影 等描述")
        if score.color_accuracy < 3:
            suggestions.append("色彩描述模糊，需指定 具体色系 或 Pantone 色号")

        return {
            "score": score.to_dict(),
            "suggestions": suggestions,
            "pass": score.overall >= self.PASS_THRESHOLD
        }

    def evaluate_with_feedback(
        self,
        prompt: str,
        feedback: Optional[List[str]] = None
    ) -> Dict:
        feedback_note = ""
        if feedback:
            feedback_note = "\n".join(f"- {f}" for f in feedback)
            feedback_note = f"\n参考之前的问题：\n{feedback_note}\n"

        eval_prompt = f"""你是一个气模设计 prompt 评分专家。请评估以下气模设计 prompt 的质量。

【待评估 Prompt】
{prompt}
{feedback_note}
【评分维度】（每项 1-5 分，5 分最优）
1. 材质准确性 (material_accuracy)：是否明确描述了材质（PVC、TPU、防水面料等）
2. 结构合理性 (structural_soundness)：是否清晰描述了充气结构、接缝、底座等
3. 视觉质量 (visual_quality)：是否有专业的视觉描述（构图、光影、8K等）
4. 颜色准确性 (color_accuracy)：是否指定了具体颜色或色系

请按以下 JSON 格式返回评分和反馈：
{{
  "material_accuracy": X,
  "structural_soundness": X,
  "visual_quality": X,
  "color_accuracy": X,
  "overall": X,
  "pass": true/false,
  "feedback": "具体改进建议（如果 pass=false，说明不足之处和如何改进）"
}}

返回 JSON："""

        try:
            import requests
            logger.info("selene_scoring", prompt=f"{prompt[:80]}...")
            resp = requests.post(
                self.SELENE_URL,
                json={
                    "messages": [{"role": "user", "content": eval_prompt}],
                    "max_tokens": 300,
                    "temperature": 0.3
                },
                timeout=60
            )
            if resp.status_code == 200:
                result_text = resp.json()["choices"][0]["message"]["content"]
                logger.info("selene_response", response=f"{result_text[:200]}...")
                return self._parse_selene_response(result_text, prompt)
        except Exception:
            pass

        return self.evaluate_and_suggest(prompt)

    def _parse_selene_response(self, response_text: str, prompt: str) -> Dict:
        try:
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                data = eval(json_match.group())
                material = float(data.get("material_accuracy", 0))
                structure = float(data.get("structural_soundness", 0))
                visual = float(data.get("visual_quality", 0))
                color = float(data.get("color_accuracy", 0))
                overall = float(data.get("overall", 0))
                feedback = data.get("feedback", "")
                passed = data.get("pass", overall >= self.PASS_THRESHOLD)

                return {
                    "score": {
                        "material_accuracy": round(material, 2),
                        "structural_soundness": round(structure, 2),
                        "visual_quality": round(visual, 2),
                        "color_accuracy": round(color, 2),
                        "overall": round(overall, 2)
                    },
                    "suggestions": [feedback] if feedback else [],
                    "pass": passed
                }
        except Exception:
            pass

        return self.evaluate_and_suggest(prompt)


_scorer: Optional[AirMoldScorer] = None


def get_scorer() -> AirMoldScorer:
    global _scorer
    if _scorer is None:
        _scorer = AirMoldScorer()
    return _scorer