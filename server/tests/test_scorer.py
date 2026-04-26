import pytest
from tools.patterns.scorer import AirMoldScorer, AirMoldScore


class TestAirMoldScore:
    def test_to_dict_returns_all_fields(self):
        score = AirMoldScore(
            material_accuracy=4.0,
            structural_soundness=3.5,
            visual_quality=4.2,
            color_accuracy=3.8,
            overall=3.875
        )
        result = score.to_dict()
        assert result["material_accuracy"] == 4.0
        assert result["structural_soundness"] == 3.5
        assert result["visual_quality"] == 4.2
        assert result["color_accuracy"] == 3.8
        assert result["overall"] == 3.875

    def test_to_dict_keys_match_fields(self):
        score = AirMoldScore(1.0, 2.0, 3.0, 4.0, 2.5)
        result = score.to_dict()
        assert set(result.keys()) == {
            "material_accuracy",
            "structural_soundness",
            "visual_quality",
            "color_accuracy",
            "overall"
        }


class TestAirMoldScorer:
    def test_score_prompt_with_material_keywords(self, sample_prompt_detailed):
        scorer = AirMoldScorer()
        score = scorer.score_prompt(sample_prompt_detailed)
        assert isinstance(score, AirMoldScore)
        assert score.material_accuracy > 0
        assert score.structural_soundness > 0

    def test_score_prompt_returns_airmoldscore(self, sample_prompt_basic):
        scorer = AirMoldScorer()
        score = scorer.score_prompt(sample_prompt_basic)
        assert isinstance(score, AirMoldScore)
        assert 0 <= score.overall <= 5.0

    def test_score_prompt_empty_string(self, sample_prompt_minimal):
        scorer = AirMoldScorer()
        score = scorer.score_prompt(sample_prompt_minimal)
        assert isinstance(score, AirMoldScore)
        assert score.overall == 0.0

    def test_score_batch_single_prompt(self, sample_prompt_basic):
        scorer = AirMoldScorer()
        results = scorer.score_batch([sample_prompt_basic])
        assert len(results) == 1
        assert isinstance(results[0], AirMoldScore)

    def test_score_batch_multiple_prompts(self, sample_prompt_basic, sample_prompt_detailed):
        scorer = AirMoldScorer()
        results = scorer.score_batch([sample_prompt_basic, sample_prompt_detailed])
        assert len(results) == 2

    def test_score_dimension_keyword_matching(self):
        scorer = AirMoldScorer()
        score = scorer._score_dimension("PVC 防水面料 耐磨", scorer.MATERIAL_KEYWORDS)
        assert score > 0

    def test_score_dimension_no_match(self):
        scorer = AirMoldScorer()
        score = scorer._score_dimension("hello world", scorer.MATERIAL_KEYWORDS)
        assert score == 0.0

    def test_score_dimension_caps_at_five(self):
        scorer = AirMoldScorer()
        long_prompt = " ".join(scorer.MATERIAL_KEYWORDS * 5)
        score = scorer._score_dimension(long_prompt, scorer.MATERIAL_KEYWORDS)
        assert score <= 5.0

    def test_evaluate_and_suggest_returns_dict(self, sample_prompt_basic):
        scorer = AirMoldScorer()
        result = scorer.evaluate_and_suggest(sample_prompt_basic)
        assert isinstance(result, dict)
        assert "score" in result
        assert "suggestions" in result
        assert "pass" in result

    def test_evaluate_and_suggest_low_score_has_suggestions(self):
        scorer = AirMoldScorer()
        result = scorer.evaluate_and_suggest("hello")
        assert isinstance(result["suggestions"], list)

    def test_evaluate_and_suggest_high_score_passes(self, sample_prompt_detailed):
        scorer = AirMoldScorer()
        result = scorer.evaluate_and_suggest(sample_prompt_detailed)
        assert result["pass"] is True

    def test_evaluate_batch(self, sample_prompt_basic, sample_prompt_chinese):
        scorer = AirMoldScorer()
        results = scorer.evaluate_batch([sample_prompt_basic, sample_prompt_chinese])
        assert len(results) == 2
        assert all("score" in r for r in results)

    def test_scorer_initialization_with_api_key(self):
        scorer = AirMoldScorer(api_key="test_key")
        assert scorer.api_key == "test_key"

    def test_scorer_initialization_without_api_key(self):
        scorer = AirMoldScorer()
        assert scorer.api_key is None
