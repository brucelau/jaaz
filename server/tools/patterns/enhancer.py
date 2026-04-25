from typing import Optional, List, Dict
from pathlib import Path
from dataclasses import dataclass, field
from .database import get_pattern_database
from .matcher import PatternMatcher, MatchedPattern


@dataclass
class EnhancementResult:
    original_input: str
    matched_patterns: List[MatchedPattern]
    filtered_patterns: List[MatchedPattern]
    enhanced_prompt: str
    enhancement_keywords: Dict
    style_reference: Optional[str] = None
    strong_patterns: List[str] = field(default_factory=list)
    template_version: str = "v1"


class PromptEnhancer:
    WEAK_THRESHOLD = 0.3
    STRONG_THRESHOLD = 0.7

    DEFAULT_TEMPLATE = """你是一个气模设计专家。根据用户需求和专业设计规范，生成专业、详细、高质量的气模设计提示词。

用户需求：{user_input}

匹配到的设计规范：
{pattern_context}{style_note}

要求：
1. 确保提示词专业、详细，符合气模设计行业水准
2. 强制包含颜色、构图、材质、光影等关键要素
3. 直接输出提示词，不包含任何解释或额外文字

输出："""

    def __init__(
        self,
        matcher: Optional[PatternMatcher] = None,
        api_key: Optional[str] = None,
        pattern_weights: Optional[Dict[str, float]] = None,
    ):
        self.matcher = matcher or PatternMatcher()
        self.api_key = api_key
        self.pattern_weights = pattern_weights or {}
        self._template = self.DEFAULT_TEMPLATE

    def get_template(self) -> str:
        return self._template

    def enhance(self, user_input: str, pattern_weights: Dict[str, float] = None) -> EnhancementResult:
        if pattern_weights:
            self.pattern_weights = pattern_weights

        matched = self.matcher.match(user_input)

        filtered, kept = self._filter_by_weight(matched)
        kept = self._sort_by_weight(kept)
        strong_patterns = [p.name for p in kept if self._get_weight(p) >= self.STRONG_THRESHOLD]

        keywords = self.matcher.get_enhancement_keywords(kept)

        if self.use_llm:
            enhanced = self._enhance_with_llm(user_input, kept, strong_patterns, keywords)
        else:
            enhanced = self._enhance_with_templates(user_input, kept, strong_patterns, keywords)

        return EnhancementResult(
            original_input=user_input,
            matched_patterns=kept,
            filtered_patterns=filtered,
            enhanced_prompt=enhanced,
            enhancement_keywords=keywords,
            strong_patterns=strong_patterns,
        )

    def _filter_by_weight(self, matched: List[MatchedPattern]) -> tuple:
        filtered = []
        kept = []
        for p in matched:
            weight = self._get_weight(p)
            if weight < self.WEAK_THRESHOLD:
                filtered.append(p)
            else:
                kept.append(p)
        return filtered, kept

    def _get_weight(self, m: MatchedPattern) -> float:
        return self.pattern_weights.get(m.name, 1.0)

    def _sort_by_weight(self, matched: List[MatchedPattern]) -> List[MatchedPattern]:
        return sorted(matched, key=self._get_weight, reverse=True)

    @property
    def use_llm(self) -> bool:
        return bool(self.api_key)

    def _enhance_with_templates(
        self,
        user_input: str,
        matched: List[MatchedPattern],
        strong_patterns: List[str],
        keywords: Dict,
    ) -> str:
        parts = [user_input]

        if keywords.get("colors"):
            colors_str = "，".join(keywords["colors"][:3])
            parts.append(f"专业配色：{colors_str}")

        if keywords.get("structure"):
            structure_str = "，".join(keywords["structure"][:3])
            parts.append(f"结构特点：{structure_str}")

        if keywords.get("composition"):
            comp_str = "，".join(keywords["composition"][:2])
            prefix = "【重点】" if "composition" in strong_patterns else ""
            parts.append(f"{prefix}构图方式：{comp_str}")

        if keywords.get("lighting"):
            light_str = "，".join(keywords["lighting"][:2])
            prefix = "【重点】" if "lighting" in strong_patterns else ""
            parts.append(f"{prefix}光影效果：{light_str}")

        if keywords.get("material"):
            mat_str = "，".join(keywords["material"][:2])
            parts.append(f"材质描写：{mat_str}")

        parts.append("专业产品摄影风格，高质量，8K分辨率")

        return "，".join(parts)

    def _enhance_with_llm(
        self,
        user_input: str,
        matched: List[MatchedPattern],
        strong_patterns: List[str],
        keywords: Dict,
    ) -> str:
        if not matched:
            return self._enhance_with_templates(user_input, matched, strong_patterns, keywords)

        pattern_context = self._build_pattern_context(matched, strong_patterns, keywords)

        prompt = self._template.format(
            user_input=user_input,
            pattern_context=pattern_context,
            style_note=""
        )

        try:
            import os
            import requests

            api_key = self.api_key or os.getenv("GEMINI_API_KEY", "")
            if not api_key:
                return self._enhance_with_templates(user_input, matched, strong_patterns, keywords)

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"

            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": 0.7, "maxOutputTokens": 500}
            }

            response = requests.post(url, json=payload, timeout=30)
            if response.status_code == 200:
                data = response.json()
                result = data["candidates"][0]["content"]["parts"][0]["text"]
                return result.strip()
        except Exception:
            pass

        return self._enhance_with_templates(user_input, matched, strong_patterns, keywords)

    def _build_pattern_context(self, matched: List[MatchedPattern], strong_patterns: List[str], keywords: Dict) -> str:
        lines = []
        prefix = "【重点】"

        style_info = [m for m in matched if m.category == "style"]
        if style_info:
            lines.append("风格规范：")
            for s in style_info:
                p = prefix if s.name in strong_patterns else ""
                lines.append(f"  {p}{s.name}：{s.pattern_data.get('description', '')}")

        product_info = [m for m in matched if m.category == "product"]
        if product_info:
            lines.append("产品规范：")
            for pr in product_info:
                pref = prefix if pr.name in strong_patterns else ""
                lines.append(f"  {pref}{pr.name}：{pr.pattern_data.get('description', '')}")

        color_info = [m for m in matched if m.category == "color"]
        if color_info:
            lines.append("色彩规范：")
            for c in color_info:
                pref = prefix if c.name in strong_patterns else ""
                lines.append(f"  {pref}{c.name}：{'，'.join(c.pattern_data.get('palette', [])[:3])}")

        if keywords.get("composition"):
            p = prefix if "composition" in strong_patterns else ""
            lines.append(f"{p}构图要素：{'，'.join(keywords['composition'][:3])}")

        if keywords.get("lighting"):
            p = prefix if "lighting" in strong_patterns else ""
            lines.append(f"{p}光影要素：{'，'.join(keywords['lighting'][:2])}")

        if keywords.get("material"):
            p = prefix if "material" in strong_patterns else ""
            lines.append(f"{p}材质要素：{'，'.join(keywords['material'][:2])}")

        return "\n".join(lines) if lines else "无特定规范"