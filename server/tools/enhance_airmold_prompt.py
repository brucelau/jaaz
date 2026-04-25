from typing import Annotated, Optional, List
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from patterns import (
    PromptEnhancer,
    PatternMatcher,
    RefinementEngine,
    get_refinement_engine,
    AirMoldScorer,
    get_scorer,
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


@tool("enhance_airmold_prompt",
      description="增强气模设计 prompt。当用户描述气模设计需求时使用此工具，可以将简单的用户描述转化为专业的图像生成 prompt。此工具基于气模设计知识库进行增强，包含材质、结构、颜色、构图等专业要素。",
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

    result = enhancer.enhance(user_input)
    enhanced = result.enhanced_prompt

    if error_feedback:
        refinement_engine = get_refinement_engine()
        enhanced = refinement_engine.refine(enhanced, error_feedback, api_key)

    return enhanced


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


__all__ = ["enhance_airmold_prompt", "refine_airmold_prompt", "score_airmold_prompt"]