"""Tests for priority scoring service."""

from app.models import KeywordData
from app.services.priority import (
    calculate_priority,
    estimate_effort,
    estimate_impact,
)


class TestPriorityScoring:
    """Test cases for priority scoring."""

    def test_high_impact_low_effort_scores_high(self):
        """Test that high impact + low effort = high priority."""
        score = calculate_priority(
            title="Fix missing H1",
            category="Structure",
            impact="high",
            effort="low",
        )

        assert score.score >= 70  # Should be high priority
        assert score.impact == "high"
        assert score.effort == "low"

    def test_low_impact_high_effort_scores_low(self):
        """Test that low impact + high effort = low priority."""
        score = calculate_priority(
            title="Comprehensive restructure",
            category="GEO",
            impact="low",
            effort="high",
        )

        assert score.score <= 50  # Should be lower priority
        assert score.impact == "low"
        assert score.effort == "high"

    def test_structure_category_weighted_higher(self):
        """Test that structure issues get higher weight."""
        structure_score = calculate_priority(
            title="Fix issue",
            category="Structure",
            impact="medium",
            effort="medium",
        )

        geo_score = calculate_priority(
            title="Fix issue",
            category="GEO",
            impact="medium",
            effort="medium",
        )

        assert structure_score.score > geo_score.score

    def test_keyword_volume_bonus(self):
        """Test that matching keywords with volume add bonus."""
        keyword_data = [
            KeywordData(keyword="seo optimization", volume=10000),
            KeywordData(keyword="content strategy", volume=5000),
        ]

        with_keyword = calculate_priority(
            title="Target SEO optimization",
            category="SEO",
            impact="medium",
            effort="medium",
            keyword_data=keyword_data,
        )

        without_keyword = calculate_priority(
            title="Generic recommendation",
            category="SEO",
            impact="medium",
            effort="medium",
            keyword_data=keyword_data,
        )

        assert with_keyword.score > without_keyword.score
        assert with_keyword.keyword_volume == 10000

    def test_factors_breakdown(self):
        """Test that score factors are tracked."""
        score = calculate_priority(
            title="Test",
            category="SEO",
            impact="high",
            effort="low",
        )

        assert "impact" in score.factors
        assert "effort" in score.factors
        assert "category" in score.factors
        assert "keyword_volume" in score.factors


class TestImpactEstimation:
    """Test cases for impact estimation."""

    def test_estimates_high_for_critical_issues(self):
        """Test high impact for critical issues."""
        assert estimate_impact("Missing H1 heading") == "high"
        assert estimate_impact("Missing meta description") == "high"
        assert estimate_impact("Thin content detected") == "high"

    def test_estimates_low_for_minor_suggestions(self):
        """Test low impact for minor suggestions."""
        assert estimate_impact("Consider adding more details") == "low"
        assert estimate_impact("Optional enhancement") == "low"
        assert estimate_impact("Minor improvement") == "low"

    def test_defaults_to_medium(self):
        """Test default medium impact for unclear text."""
        assert estimate_impact("Update the content") == "medium"
        assert estimate_impact("Improve structure") == "medium"


class TestEffortEstimation:
    """Test cases for effort estimation."""

    def test_estimates_low_for_simple_changes(self):
        """Test low effort for simple changes."""
        assert estimate_effort("Add meta description") == "low"
        assert estimate_effort("Update title tag") == "low"
        assert estimate_effort("Fix heading") == "low"

    def test_estimates_high_for_complex_changes(self):
        """Test high effort for complex changes."""
        assert estimate_effort("Restructure entire content") == "high"
        assert estimate_effort("Create new comprehensive guide") == "high"
        assert estimate_effort("Rewrite multiple pages") == "high"

    def test_defaults_to_medium(self):
        """Test default medium effort for unclear text."""
        assert estimate_effort("Improve SEO") == "medium"
        assert estimate_effort("Optimize content") == "medium"
