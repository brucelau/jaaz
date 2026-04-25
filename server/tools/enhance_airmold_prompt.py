from typing import Annotated
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from patterns import PromptEnhancer, PatternMatcher


_patterns_matcher = PatternMatcher()
_patterns_enhancer = PromptEnhancer(matcher=_patterns_matcher)


class EnhancePromptInputSchema(BaseModel):
    user_input: str = Field(
        description="Required. The user's design brief or description for air-mold design. Example: '一个卡通风格的红色大气模'"
    )


@tool("enhance_airmold_prompt",
      description="增强气模设计 prompt。当用户描述气模设计需求时使用此工具，可以将简单的用户描述转化为专业的图像生成 prompt。此工具基于气模设计知识库进行增强，包含材质、结构、颜色、构图等专业要素。",
      args_schema=EnhancePromptInputSchema)
async def enhance_airmold_prompt(
    user_input: str,
    config: RunnableConfig,
) -> str:
    """
    增强气模设计 prompt 的工具函数

    Args:
        user_input: 用户的设计需求描述
        config: LangGraph 运行配置

    Returns:
        增强后的专业 prompt
    """
    ctx = config.get('configurable', {})
    api_key = ctx.get('api_key', None)

    if api_key:
        enhancer = PromptEnhancer(matcher=_patterns_matcher, api_key=api_key)
    else:
        enhancer = _patterns_enhancer

    result = enhancer.enhance(user_input)

    return result.enhanced_prompt


__all__ = ["enhance_airmold_prompt"]