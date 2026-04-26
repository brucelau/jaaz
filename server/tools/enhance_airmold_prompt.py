from typing import Annotated, Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from tools.patterns import (
    PromptEnhancer,
    PatternMatcher,
    RefinementEngine,
    get_refinement_engine,
    AirMoldScorer,
    get_scorer,
    VQAChecker,
    get_vqa_checker,
)


_patterns_matcher = PatternMatcher()
_patterns_enhancer = PromptEnhancer(matcher=_patterns_matcher)


class EnhancePromptInputSchema(BaseModel):
    user_input: str = Field(
        description="Required. The user's design brief or description for air-mold design. Example: '一个卡通风格的红色大气模'"
    )
    error_feedback: Optional[List[str]] = Field(
        default=None,
        description="Optional. List of error feedback from previous generation attempts. If provided, the prompt will be refined based on these errors."
    )


class RefinePromptInputSchema(BaseModel):
    prompt: str = Field(
        description="Required. The current prompt to refine"
    )
    error_feedback: List[str] = Field(
        description="Required. List of errors from previous generation"
    )


class ScorePromptInputSchema(BaseModel):
    prompt: str = Field(
        description="Required. The prompt to score"
    )


class CheckImageInputSchema(BaseModel):
    image_path: str = Field(
        description="Required. Path to the generated image to check"
    )
    prompt: str = Field(
        description="Required. The original prompt used for generation"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Optional. Categories to check: material, structure, color, visual"
    )


@tool("enhance_airmold_prompt",
      description="增强气模设计 prompt。当用户描述气模设计需求时使用此工具，可以将简单的用户描述转化为专业的图像生成 prompt。此工具基于气模设计知识库进行增强，结合 LLM 评分反馈迭代优化（最多3次），确保生成的 prompt 质量达标。",
      args_schema=EnhancePromptInputSchema)
async def enhance_airmold_prompt(
    user_input: str,
    config: RunnableConfig,
    error_feedback: Optional[List[str]] = None,
) -> str:
    ctx = config.get('configurable', {})
    api_key = ctx.get('api_key', None)

    if api_key:
        enhancer = PromptEnhancer(matcher=_patterns_matcher, api_key=api_key)
    else:
        enhancer = _patterns_enhancer

    scorer = get_scorer()

    max_retries = 3
    best_prompt = None
    best_score_info = None
    all_feedback = []

    print(f"\n{'='*60}")
    print(f"[Enhance Flow] Input: {user_input}")
    print(f"{'='*60}")

    for attempt in range(max_retries):
        feedback = all_feedback[-1:] if attempt > 0 and all_feedback else None

        print(f"\n[Attempt {attempt + 1}] Generating candidate...")
        result = enhancer.enhance(user_input, feedback=feedback)
        candidate = result.enhanced_prompt
        print(f"[Attempt {attempt + 1}] Candidate: {candidate[:100]}...")

        print(f"[Attempt {attempt + 1}] Calling Selene to score...")
        eval_result = scorer.evaluate_with_feedback(candidate, feedback)
        score = eval_result["score"]

        print(f"[Attempt {attempt + 1}] Selene Score: material={score['material_accuracy']}, structural={score['structural_soundness']}, visual={score['visual_quality']}, color={score['color_accuracy']}, overall={score['overall']}")
        print(f"[Attempt {attempt + 1}] Pass: {eval_result['pass']}")

        if eval_result["pass"]:
            print(f"[Attempt {attempt + 1}] ACCEPTED!")
            best_prompt = candidate
            best_score_info = eval_result
            break

        if eval_result["suggestions"]:
            suggestion = eval_result["suggestions"][0]
            print(f"[Attempt {attempt + 1}] Feedback: {suggestion}")
            all_feedback.append(suggestion)

        best_prompt = candidate

    print(f"\n[Final] Selected: {best_prompt[:100]}...")
    print(f"{'='*60}\n")

    if best_prompt is None:
        best_prompt = user_input

    if error_feedback:
        refinement_engine = get_refinement_engine()
        best_prompt = refinement_engine.refine(best_prompt, error_feedback, api_key)

    return best_prompt


@tool("refine_airmold_prompt",
      description="基于错误反馈修正气模设计 prompt。当图像生成结果有错误时，使用此工具修正 prompt。",
      args_schema=RefinePromptInputSchema)
async def refine_airmold_prompt(
    prompt: str,
    error_feedback: List[str],
    config: RunnableConfig,
) -> str:
    ctx = config.get('configurable', {})
    api_key = ctx.get('api_key', None)

    refinement_engine = get_refinement_engine()
    return refinement_engine.refine(prompt, error_feedback, api_key)


@tool("score_airmold_prompt",
      description="评估气模设计 prompt 质量。基于材质准确性、结构合理性、视觉质量、颜色准确性四个维度评分。",
      args_schema=ScorePromptInputSchema)
async def score_airmold_prompt(
    prompt: str,
    config: RunnableConfig,
) -> str:
    scorer = get_scorer()
    evaluation = scorer.evaluate_and_suggest(prompt)

    score = evaluation["score"]
    suggestions = evaluation["suggestions"]
    passed = evaluation["pass"]

    result = f"""气模设计 Prompt 评分结果：

【评分详情】
- 材质准确性: {score['material_accuracy']:.1f}/5.0
- 结构合理性: {score['structural_soundness']:.1f}/5.0
- 视觉质量: {score['visual_quality']:.1f}/5.0
- 颜色准确性: {score['color_accuracy']:.1f}/5.0

【综合评分】: {score['overall']:.1f}/5.0 ({'通过' if passed else '需改进'})

"""
    if suggestions:
        result += "【改进建议】\n" + "\n".join(f"- {s}" for s in suggestions)

    return result


@tool("check_airmold_image",
      description="检查气模图像质量。使用 VQA 检查生成的图像是否符合 prompt 描述，返回错误反馈列表。",
      args_schema=CheckImageInputSchema)
async def check_airmold_image(
    image_path: str,
    prompt: str,
    config: RunnableConfig,
    categories: Optional[List[str]] = None,
) -> str:
    ctx = config.get('configurable', {})
    api_key = ctx.get('api_key', None)

    checker = get_vqa_checker(api_key)
    errors = checker.check_image(image_path, prompt, categories)
    feedback = checker.get_error_feedback(errors)

    if not feedback:
        return "图像检查通过：未发现明显错误。"

    result = "【图像检查结果】\n\n"
    result += "发现以下问题：\n"
    for i, fb in enumerate(feedback, 1):
        result += f"{i}. {fb}\n"

    result += "\n可以使用 refine_airmold_prompt 工具结合这些错误反馈来优化 prompt。"

    return result


__all__ = [
    "enhance_airmold_prompt",
    "refine_airmold_prompt",
    "score_airmold_prompt",
    "check_airmold_image",
]