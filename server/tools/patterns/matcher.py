from dataclasses import dataclass
from typing import Optional, Dict, List
from .database import PatternDatabase, get_pattern_database


@dataclass
class MatchedPattern:
    category: str
    name: str
    score: float
    matched_keywords: List[str]
    pattern_data: Dict


class PatternMatcher:
    def __init__(self, db: Optional[PatternDatabase] = None):
        self.db = db or get_pattern_database()

    def match(self, user_input: str) -> List[MatchedPattern]:
        input_lower = user_input.lower()
        words = input_lower.replace(",", " ").replace("，", " ").split()
        matched = []

        matched.extend(self._match_styles(input_lower, words))
        matched.extend(self._match_products(input_lower, words))
        matched.extend(self._match_colors(input_lower, words))

        matched.sort(key=lambda x: x.score, reverse=True)
        return matched

    def _match_styles(self, input_lower: str, words: List[str]) -> List[MatchedPattern]:
        matched = []
        for name, pattern in self.db.styles.items():
            score = 0.0
            matched_kw = []

            for kw in pattern.keywords:
                if kw in input_lower:
                    score += 1.0
                    matched_kw.append(kw)

            for word in words:
                for kw in pattern.keywords:
                    if kw in word or word in kw:
                        score += 0.5
                        if kw not in matched_kw:
                            matched_kw.append(kw)

            if score > 0:
                matched.append(MatchedPattern(
                    category="style",
                    name=name,
                    score=score,
                    matched_keywords=matched_kw,
                    pattern_data={
                        "colors": pattern.colors,
                        "composition": pattern.composition,
                        "lighting": pattern.lighting,
                        "description": pattern.description,
                    }
                ))
        return matched

    def _match_products(self, input_lower: str, words: List[str]) -> List[MatchedPattern]:
        matched = []
        for name, pattern in self.db.products.items():
            score = 0.0
            matched_kw = []

            for kw in pattern.keywords:
                if kw in input_lower:
                    score += 1.5
                    matched_kw.append(kw)

            for word in words:
                for kw in pattern.keywords:
                    if kw in word or word in kw:
                        score += 0.5
                        if kw not in matched_kw:
                            matched_kw.append(kw)

            if score > 0:
                matched.append(MatchedPattern(
                    category="product",
                    name=name,
                    score=score,
                    matched_keywords=matched_kw,
                    pattern_data={
                        "structure": pattern.structure,
                        "material": pattern.material,
                        "details": pattern.details,
                        "composition": pattern.composition,
                        "description": pattern.description,
                    }
                ))
        return matched

    def _match_colors(self, input_lower: str, words: List[str]) -> List[MatchedPattern]:
        matched = []
        for name, pattern in self.db.colors.items():
            score = 0.0
            matched_kw = []

            color_keywords = [name, pattern.description[:10] if pattern.description else ""]
            for kw in color_keywords:
                if kw and kw in input_lower:
                    score += 1.0
                    matched_kw.append(kw)

            for palette_item in pattern.palette:
                if palette_item in input_lower:
                    score += 0.5
                    matched_kw.append(palette_item)

            if score > 0:
                matched.append(MatchedPattern(
                    category="color",
                    name=name,
                    score=score,
                    matched_keywords=matched_kw,
                    pattern_data={
                        "palette": pattern.palette,
                        "matching": pattern.matching,
                        "description": pattern.description,
                    }
                ))
        return matched

    def get_enhancement_keywords(self, matched: List[MatchedPattern]) -> Dict[str, List[str]]:
        result = {
            "colors": [],
            "composition": [],
            "lighting": [],
            "material": [],
            "structure": [],
            "details": [],
        }

        for m in matched:
            if m.category == "style":
                result["colors"].extend(m.pattern_data.get("colors", []))
                result["composition"].extend(m.pattern_data.get("composition", []))
                result["lighting"].extend(m.pattern_data.get("lighting", []))

            elif m.category == "product":
                result["structure"].extend(m.pattern_data.get("structure", []))
                result["material"].extend(m.pattern_data.get("material", []))
                result["details"].extend(m.pattern_data.get("details", []))
                result["composition"].extend(m.pattern_data.get("composition", []))

            elif m.category == "color":
                result["colors"].extend(m.pattern_data.get("palette", []))

        for key in result:
            result[key] = list(set(result[key]))

        return result