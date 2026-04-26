import pytest
from tools.patterns.scorer import AirMoldScorer


class TestAirMoldScorer:
    def test_scorer_initialization_with_api_key(self):
        scorer = AirMoldScorer(api_key="test_key")
        assert scorer.api_key == "test_key"

    def test_scorer_initialization_without_api_key(self):
        scorer = AirMoldScorer()
        assert scorer.api_key is None

    def test_template_loading(self):
        scorer = AirMoldScorer()
        template = scorer.get_template()
        assert isinstance(template, str)
        assert len(template) > 0
        assert "评分维度" in template

    @pytest.mark.skip(reason="需要 Selene 服务")
    def test_evaluate_with_feedback_returns_dict(self):
        scorer = AirMoldScorer()
        result = scorer.evaluate_with_feedback("test prompt")
        assert isinstance(result, dict)
        assert "score" in result
        assert "suggestions" in result
        assert "pass" in result

    @pytest.mark.skip(reason="需要 Selene 服务")
    def test_score_has_all_dimensions(self):
        scorer = AirMoldScorer()
        result = scorer.evaluate_with_feedback("test prompt")
        score = result["score"]
        expected_keys = [
            "material_accuracy",
            "inflatable_structure",
            "festival_theme",
            "style",
            "main_shape",
            "product_elements",
            "usage_scene",
            "time_setting",
            "lighting_effect",
            "atmosphere",
            "background",
            "composition",
            "visual_quality",
            "color_accuracy",
            "overall"
        ]
        assert set(score.keys()) == set(expected_keys)
