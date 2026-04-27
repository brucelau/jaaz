import base64
import json
from typing import List, Dict, Optional, Tuple
from pathlib import Path


class VQAChecker:
    QA_TEMPLATE = """你是一个专业的图像质量检查员。请根据图像和描述，检查以下问题。

描述：{prompt}

问题列表：
{questions}

要求：
1. 对每个问题回答 YES 或 NO
2. 如果回答 NO，请用一句话描述具体错误
3. 严格检查，不要放过任何问题

格式：
问题1: YES/NO. [如果NO，描述错误]
问题2: YES/NO. [如果NO，描述错误]
..."""

    MATERIAL_QUESTIONS = [
        "气模材质是否像 PVC 或其他塑料材质？",
        "表面是否有合适的光泽度？",
        "材质质感是否与描述一致？",
    ]

    STRUCTURE_QUESTIONS = [
        "充气结构是否明显可见？",
        "接缝位置是否合理？",
        "整体比例是否协调？",
    ]

    COLOR_QUESTIONS = [
        "主色调是否与描述一致？",
        "颜色是否鲜艳饱满？",
        "是否存在色差问题？",
    ]

    VISUAL_QUESTIONS = [
        "构图是否专业？",
        "光影效果是否合理？",
        "背景是否整洁？",
    ]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key

    def check_image(
        self,
        image_path: str,
        prompt: str,
        categories: Optional[List[str]] = None
    ) -> Dict[str, List[str]]:
        if categories is None:
            categories = ["material", "structure", "color", "visual"]

        questions = self._build_questions(categories)
        qa_result = self._query_vqa(image_path, prompt, questions)

        errors = self._extract_errors(qa_result, categories)
        return errors

    def _build_questions(self, categories: List[str]) -> str:
        all_questions = []
        for i, cat in enumerate(categories):
            if cat == "material":
                for q in self.MATERIAL_QUESTIONS:
                    all_questions.append(f"材质-{q}")
            elif cat == "structure":
                for q in self.STRUCTURE_QUESTIONS:
                    all_questions.append(f"结构-{q}")
            elif cat == "color":
                for q in self.COLOR_QUESTIONS:
                    all_questions.append(f"颜色-{q}")
            elif cat == "visual":
                for q in self.VISUAL_QUESTIONS:
                    all_questions.append(f"视觉-{q}")

        return "\n".join(f"{i+1}. {q}" for i, q in enumerate(all_questions))

    def _query_vqa(
        self,
        image_path: str,
        prompt: str,
        questions: str
    ) -> str:
        if not self.api_key:
            return self._rule_based_check(prompt, questions)

        try:
            import os
            import requests

            with open(image_path, "rb") as f:
                image_b64 = base64.b64encode(f.read()).decode("utf-8")

            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"

            payload = {
                "contents": [{
                    "parts": [
                        {"text": self.QA_TEMPLATE.format(prompt=prompt, questions=questions)},
                        {"inline_data": {"mime_type": "image/png", "data": image_b64}}
                    ]
                }],
                "generationConfig": {"temperature": 0.1, "maxOutputTokens": 500}
            }

            response = requests.post(url, json=payload, timeout=60)
            if response.status_code == 200:
                data = response.json()
                return data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass

        return self._rule_based_check(prompt, questions)

    def _rule_based_check(self, prompt: str, questions: str) -> str:
        prompt_lower = prompt.lower()
        results = []

        for line in questions.split("\n"):
            if not line.strip():
                continue
            q_id = line.split(".")[0] if "." in line else line
            q_text = line

            if "材质" in q_text:
                if any(kw in prompt_lower for kw in ["pvc", "光滑", "防水", "材质"]):
                    results.append(f"{q_id}. YES")
                else:
                    results.append(f"{q_id}. NO. 材质描述不够具体")
            elif "结构" in q_text:
                if any(kw in prompt_lower for kw in ["充气", "立体", "接缝", "结构"]):
                    results.append(f"{q_id}. YES")
                else:
                    results.append(f"{q_id}. NO. 结构描述缺失")
            elif "颜色" in q_text:
                if any(kw in prompt_lower for kw in ["红色", "蓝色", "绿色", "黄色", "色"]):
                    results.append(f"{q_id}. YES")
                else:
                    results.append(f"{q_id}. NO. 颜色描述不够具体")
            elif "视觉" in q_text or "构图" in q_text or "光影" in q_text:
                if any(kw in prompt_lower for kw in ["构图", "光影", "摄影", "背景", "专业"]):
                    results.append(f"{q_id}. YES")
                else:
                    results.append(f"{q_id}. NO. 视觉描述不够专业")

        return "\n".join(results)

    def _extract_errors(
        self,
        qa_result: str,
        categories: List[str]
    ) -> Dict[str, List[str]]:
        errors = {cat: [] for cat in categories}

        for line in qa_result.split("\n"):
            if not line.strip():
                continue

            line_lower = line.lower()
            if "no." in line_lower or "no," in line_lower:
                error_desc = line.split(".", 1)[1].strip() if "." in line else line

                if "材质" in line:
                    errors["material"].append(error_desc)
                elif "结构" in line:
                    errors["structure"].append(error_desc)
                elif "颜色" in line:
                    errors["color"].append(error_desc)
                elif "视觉" in line or "构图" in line or "光影" in line:
                    errors["visual"].append(error_desc)

        return errors

    def get_error_feedback(self, errors: Dict[str, List[str]]) -> List[str]:
        feedback = []
        for category, errs in errors.items():
            for err in errs:
                if category == "material":
                    feedback.append(f"材质错误: {err}")
                elif category == "structure":
                    feedback.append(f"结构错误: {err}")
                elif category == "color":
                    feedback.append(f"颜色错误: {err}")
                elif category == "visual":
                    feedback.append(f"视觉错误: {err}")
        return feedback


_vqa_checker: Optional[VQAChecker] = None


def get_vqa_checker(api_key: Optional[str] = None) -> VQAChecker:
    global _vqa_checker
    if _vqa_checker is None or api_key is not None:
        _vqa_checker = VQAChecker(api_key=api_key)
    return _vqa_checker