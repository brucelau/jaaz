import pytest
from unittest.mock import patch
from agents.tools.patterns.enhancer import PromptEnhancer, EnhancementResult


class TestEnhancementResult:
    def test_creation(self):
        result = EnhancementResult(
            original_input="test input",
            matched_patterns=[],
            filtered_patterns=[],
            enhanced_prompt="enhanced output"
        )
        assert result.original_input == "test input"
        assert result.enhanced_prompt == "enhanced output"

    def test_matched_patterns_empty(self):
        result = EnhancementResult(
            original_input="test",
            matched_patterns=[],
            filtered_patterns=[],
            enhanced_prompt="out"
        )
        assert result.matched_patterns == []
        assert result.filtered_patterns == []


class TestPromptEnhancer:
    def test_init_with_api_key(self):
        enhancer = PromptEnhancer(api_key="test_key")
        assert enhancer.api_key == "test_key"

    def test_init_without_api_key(self):
        from agents.tools.patterns.enhancer import PromptEnhancer
        with patch.object(PromptEnhancer, 'CONFIG_PATH') as mock_path:
            mock_path.exists.return_value = False
            enhancer = PromptEnhancer()
            assert not enhancer.api_key

    @pytest.mark.asyncio
    async def test_enhance_returns_enhancement_result(self):
        enhancer = PromptEnhancer(api_key="fake_key")
        result = await enhancer.enhance("test prompt")
        assert isinstance(result, EnhancementResult)
        assert result.original_input == "test prompt"

    def test_template_loading(self):
        enhancer = PromptEnhancer()
        template = enhancer.get_template()
        assert isinstance(template, str)
        assert len(template) > 0
        assert "约束" in template or "用户需求" in template


class TestPromptEnhancerWithGemini:
    def test_enhance_with_gemini(self):
        import os
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            pytest.skip("GEMINI_API_KEY not set")

        enhancer = PromptEnhancer(api_key=api_key)
        enhancer.GEMINI_MODEL = "gemini-2.5-flash"
        result = enhancer.enhance("一个圣诞节充气装饰")

        assert isinstance(result.enhanced_prompt, str)
        assert len(result.enhanced_prompt) > 10
        assert "8K" in result.enhanced_prompt or "分辨率" in result.enhanced_prompt
