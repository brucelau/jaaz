import json
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class RefinementEngine:
    DEFAULT_REFINE_TEMPLATE = """你是一个气模设计 Prompt 优化专家。

任务：根据图像生成结果的错误反馈，优化原始 Prompt。

原始 Prompt：
{original_prompt}

错误类型：{error_type}
错误描述：{error_description}

优化策略：{refinement_strategy}
示例：{example}

要求：
1. 只修改与错误相关的部分，保持其他内容不变
2. 最小化改动，只精确修正问题点
3. 优化后的 Prompt 必须更符合生成模型的理解习惯
4. 直接输出优化后的 Prompt，不包含解释

输出："""

    def __init__(self, error_patterns_path: Optional[Path] = None):
        if error_patterns_path is None:
            error_patterns_path = Path(__file__).parent / "error_patterns.json"
        self.error_patterns = self._load_error_patterns(error_patterns_path)

    def _load_error_patterns(self, path: Path) -> Dict:
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def get_refinement_context(self, error_type: str) -> Dict:
        pattern = self.error_patterns.get(error_type, {})
        return {
            "refinement": pattern.get("refinement", ""),
            "example": pattern.get("example", ""),
        }

    def refine(
        self,
        prompt: str,
        error_feedback: List[str],
        api_key: Optional[str] = None
    ) -> str:
        if not error_feedback:
            return prompt

        if api_key:
            return self._refine_with_llm(prompt, error_feedback, api_key)
        else:
            return self._refine_with_rules(prompt, error_feedback)

    def _refine_with_rules(self, prompt: str, error_feedback: List[str]) -> str:
        refined = prompt
        for error in error_feedback:
            error_type = self._classify_error(error)
            if error_type and error_type in self.error_patterns:
                refinement = self.error_patterns[error_type]["refinement"]
                example = self.error_patterns[error_type]["example"]
                refined = self._apply_refinement(refined, error, refinement, example)
        return refined

    def _classify_error(self, error: str) -> Optional[str]:
        error_lower = error.lower()
        keywords_map = {
            "数量": "Quantity Errors",
            "个数": "Quantity Errors",
            "材质": "Material Errors",
            "面料": "Material Errors",
            "颜色": "Color Errors",
            "色": "Color Errors",
            "纹理": "Texture Errors",
            "表面": "Texture Errors",
            "形状": "Shape Errors",
            "比例": "Proportion Errors",
            "大小": "Proportion Errors",
            "结构": "Structure Errors",
            "充气": "Structure Errors",
            "光": "Lighting Errors",
            "阴影": "Shadow Errors",
            "风格": "Style Errors",
            "构图": "Composition Errors",
            "背景": "Background Errors",
            "细节": "Detail Errors",
            "安全": "Safety Errors",
            "耐用": "Durability Errors",
            "安装": "Installation Errors",
            "品牌": "Brand Errors",
            "标识": "Brand Errors",
            "可见": "Visibility Errors",
            "醒目": "Visibility Errors",
            "耐候": "Weather Resistance Errors",
            "户外": "Weather Resistance Errors",
        }
        for keyword, error_type in keywords_map.items():
            if keyword in error_lower:
                return error_type
        return None

    def _apply_refinement(
        self,
        prompt: str,
        error: str,
        refinement: str,
        example: str
    ) -> str:
        return prompt

    def _refine_with_llm(
        self,
        prompt: str,
        error_feedback: List[str],
        api_key: str
    ) -> str:
        error_contexts = []
        for error in error_feedback:
            error_type = self._classify_error(error)
            if error_type and error_type in self.error_patterns:
                pattern = self.error_patterns[error_type]
                error_contexts.append(
                    f"错误类型: {error_type}\n"
                    f"描述: {error}\n"
                    f"优化策略: {pattern['refinement']}"
                )

        if not error_contexts:
            return prompt

        context_str = "\n---\n".join(error_contexts)
        error_description = "\n".join(f"- {e}" for e in error_feedback)

        prompt_template = self.DEFAULT_REFINE_TEMPLATE.format(
            original_prompt=prompt,
            error_type="\n".join(set(self._classify_error(e) or "Unknown" for e in error_feedback)),
            error_description=error_description,
            refinement_strategy="\n".join(p.get("refinement", "") for p in [
                self.error_patterns.get(self._classify_error(e), {})
                for e in error_feedback
            ] if p),
            example="\n".join(p.get("example", "") for p in [
                self.error_patterns.get(self._classify_error(e), {})
                for e in error_feedback
            ] if p)[:200]
        )

        try:
            import os
            import requests

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

            payload = {
                "contents": [{"parts": [{"text": prompt_template}]}],
                "generationConfig": {"temperature": 0.3, "maxOutputTokens": 300}
            }

            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                result = data["candidates"][0]["content"]["parts"][0]["text"]
                return result.strip()
        except Exception:
            pass

        return self._refine_with_rules(prompt, error_feedback)


_refinement_engine: Optional[RefinementEngine] = None


def get_refinement_engine() -> RefinementEngine:
    global _refinement_engine
    if _refinement_engine is None:
        _refinement_engine = RefinementEngine()
    return _refinement_engine