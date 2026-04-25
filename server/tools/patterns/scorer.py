from dataclasses import dataclass
from typing import List, Dict, Optional
import base64


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
            suggestions.append("建议添加材质描述，如PVC材质、防水面料等")
        if score.structural_soundness < 3:
            suggestions.append("建议添加结构描述，如充气设计、接缝加固等")
        if score.visual_quality < 3:
            suggestions.append("建议添加视觉描述，如专业摄影风格、8K分辨率等")
        if score.color_accuracy < 3:
            suggestions.append("建议添加颜色描述，如具体色系或Pantone色号")

        return {
            "score": score.to_dict(),
            "suggestions": suggestions,
            "pass": score.overall >= 3.5
        }


_scorer: Optional[AirMoldScorer] = None


def get_scorer() -> AirMoldScorer:
    global _scorer
    if _scorer is None:
        _scorer = AirMoldScorer()
    return _scorer