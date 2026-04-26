import pytest
from tools.patterns.enhancer import PromptEnhancer, EnhancementResult, EnhancementCandidate
from tools.patterns.matcher import PatternMatcher


class TestEnhancementResult:
    def test_creation_with_required_fields(self):
        result = EnhancementResult(
            original_input="test input",
            matched_patterns=[],
            filtered_patterns=[],
            enhanced_prompt="enhanced output"
        )
        assert result.original_input == "test input"
        assert result.enhanced_prompt == "enhanced output"
        assert result.candidates == []

    def test_candidates_default_empty(self):
        result = EnhancementResult(
            original_input="test",
            matched_patterns=[],
            filtered_patterns=[],
            enhanced_prompt="out"
        )
        assert result.candidates == []

    def test_enhancement_keywords_default_empty(self):
        result = EnhancementResult(
            original_input="test",
            matched_patterns=[],
            filtered_patterns=[],
            enhanced_prompt="out"
        )
        assert result.enhancement_keywords == {}


class TestEnhancementCandidate:
    def test_creation(self):
        candidate = EnhancementCandidate(
            prompt="enhanced prompt",
            reason="test reason"
        )
        assert candidate.prompt == "enhanced prompt"
        assert candidate.reason == "test reason"


class TestPromptEnhancer:
    def test_init_with_default_matcher(self):
        enhancer = PromptEnhancer()
        assert isinstance(enhancer.matcher, PatternMatcher)

    def test_init_with_custom_matcher(self):
        matcher = PatternMatcher()
        enhancer = PromptEnhancer(matcher=matcher)
        assert enhancer.matcher is matcher

    def test_init_with_api_key(self):
        enhancer = PromptEnhancer(api_key="test_key")
        assert enhancer.api_key == "test_key"
        assert enhancer.use_llm is True

    def test_init_without_api_key(self):
        enhancer = PromptEnhancer()
        assert enhancer.api_key is None
        assert enhancer.use_llm is False

    def test_enhance_returns_enhancement_result(self, sample_prompt_basic):
        enhancer = PromptEnhancer()
        result = enhancer.enhance(sample_prompt_basic)
        assert isinstance(result, EnhancementResult)
        assert result.original_input == sample_prompt_basic

    def test_enhance_includes_matched_patterns(self, sample_prompt_basic):
        enhancer = PromptEnhancer()
        result = enhancer.enhance(sample_prompt_basic)
        assert isinstance(result.matched_patterns, list)

    def test_enhance_includes_enhanced_prompt(self, sample_prompt_basic):
        enhancer = PromptEnhancer()
        result = enhancer.enhance(sample_prompt_basic)
        assert isinstance(result.enhanced_prompt, str)
        assert len(result.enhanced_prompt) > 0

    def test_enhance_with_empty_input(self, sample_prompt_minimal):
        enhancer = PromptEnhancer()
        result = enhancer.enhance(sample_prompt_minimal)
        assert isinstance(result, EnhancementResult)

    def test_enhance_with_chinese_input(self, sample_prompt_chinese):
        enhancer = PromptEnhancer()
        result = enhancer.enhance(sample_prompt_chinese)
        assert isinstance(result, EnhancementResult)
        assert result.enhanced_prompt is not None

    def test_enhance_multi_returns_enhancement_result(self, sample_prompt_basic):
        enhancer = PromptEnhancer()
        result = enhancer.enhance_multi(sample_prompt_basic, num_candidates=3)
        assert isinstance(result, EnhancementResult)

    def test_enhance_multi_candidates_count(self, sample_prompt_basic):
        enhancer = PromptEnhancer()
        result = enhancer.enhance_multi(sample_prompt_basic, num_candidates=3)
        assert isinstance(result.candidates, list)

    def test_filter_by_weight_threshold(self):
        enhancer = PromptEnhancer(pattern_weights={"test1": 0.8, "test2": 0.1})
        from tools.patterns.matcher import MatchedPattern
        matched = [
            MatchedPattern(name="test1", category="style", score=0.8, matched_keywords=[], pattern_data={}),
            MatchedPattern(name="test2", category="style", score=0.1, matched_keywords=[], pattern_data={}),
        ]
        filtered, kept = enhancer._filter_by_weight(matched)
        assert len(filtered) == 1
        assert len(kept) == 1

    def test_filter_by_weight_empty_list(self):
        enhancer = PromptEnhancer()
        filtered, kept = enhancer._filter_by_weight([])
        assert filtered == []
        assert kept == []

    def test_sort_by_weight(self):
        enhancer = PromptEnhancer(pattern_weights={"low": 0.2, "high": 0.9, "mid": 0.5})
        from tools.patterns.matcher import MatchedPattern
        matched = [
            MatchedPattern(name="low", category="style", score=0.2, matched_keywords=[], pattern_data={}),
            MatchedPattern(name="high", category="style", score=0.9, matched_keywords=[], pattern_data={}),
            MatchedPattern(name="mid", category="style", score=0.5, matched_keywords=[], pattern_data={}),
        ]
        sorted_matched = enhancer._sort_by_weight(matched)
        assert enhancer._get_weight(sorted_matched[0]) >= enhancer._get_weight(sorted_matched[1]) >= enhancer._get_weight(sorted_matched[2])

    def test_get_weight_default(self):
        enhancer = PromptEnhancer()
        from tools.patterns.matcher import MatchedPattern
        m = MatchedPattern(name="test", category="style", score=0.5, matched_keywords=[], pattern_data={})
        assert enhancer._get_weight(m) == 1.0

    def test_get_weight_custom(self):
        enhancer = PromptEnhancer(pattern_weights={"test": 0.3})
        from tools.patterns.matcher import MatchedPattern
        m = MatchedPattern(name="test", category="style", score=0.5, matched_keywords=[], pattern_data={})
        assert enhancer._get_weight(m) == 0.3

    def test_template_loading(self):
        enhancer = PromptEnhancer()
        template = enhancer.get_template()
        assert isinstance(template, str)
        assert len(template) > 0

    def test_enhance_with_templates_fallback(self, sample_prompt_basic):
        enhancer = PromptEnhancer()
        from tools.patterns.matcher import MatchedPattern
        result = enhancer._enhance_with_templates(
            sample_prompt_basic,
            matched=[],
            strong_patterns=[],
            keywords={}
        )
        assert isinstance(result, str)
