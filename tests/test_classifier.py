"""Tests for content classification service."""

from app.models import AEOAnalysis, ContentType, GEOAnalysis, SEOAnalysis
from app.services.classifier import classify_content


class TestContentClassifier:
    """Test cases for content classifier."""

    def create_seo_analysis(self, score: int) -> SEOAnalysis:
        """Create SEO analysis with given score."""
        return SEOAnalysis(
            primary_topic="Test",
            target_keywords=[],
            missing_keywords=[],
            content_gaps=[],
            cluster_opportunities=[],
            quality_score=score,
            quality_rationale="Test",
            recommendations=[],
        )

    def create_aeo_analysis(self, score: int) -> AEOAnalysis:
        """Create AEO analysis with given score."""
        return AEOAnalysis(
            questions_answered=[],
            questions_to_add=[],
            paa_opportunities=[],
            featured_snippet_potential="Test",
            format_quality="Test",
            readiness_score=score,
            readiness_rationale="Test",
            recommendations=[],
        )

    def create_geo_analysis(self, score: int) -> GEOAnalysis:
        """Create GEO analysis with given score."""
        return GEOAnalysis(
            originality_assessment="Test",
            citation_worthy_elements=[],
            absorption_risks=[],
            defensibility_suggestions=[],
            strength_score=score,
            strength_rationale="Test",
            recommendations=[],
        )

    def test_all_strong_classified_as_all(self):
        """Test content strong in all areas is classified as ALL."""
        result = classify_content(
            seo=self.create_seo_analysis(8),
            aeo=self.create_aeo_analysis(8),
            geo=self.create_geo_analysis(8),
        )

        assert result.primary_type == ContentType.ALL
        assert result.confidence >= 0.85
        assert ContentType.SEO in result.overlapping_types
        assert ContentType.AEO in result.overlapping_types
        assert ContentType.GEO in result.overlapping_types

    def test_seo_aeo_strong_classified_correctly(self):
        """Test content strong in SEO and AEO."""
        result = classify_content(
            seo=self.create_seo_analysis(8),
            aeo=self.create_aeo_analysis(8),
            geo=self.create_geo_analysis(4),
        )

        assert result.primary_type == ContentType.SEO_AEO
        assert ContentType.SEO in result.overlapping_types
        assert ContentType.AEO in result.overlapping_types
        assert ContentType.GEO not in result.overlapping_types

    def test_seo_geo_strong_classified_correctly(self):
        """Test content strong in SEO and GEO."""
        result = classify_content(
            seo=self.create_seo_analysis(8),
            aeo=self.create_aeo_analysis(4),
            geo=self.create_geo_analysis(8),
        )

        assert result.primary_type == ContentType.SEO_GEO

    def test_aeo_geo_strong_classified_correctly(self):
        """Test content strong in AEO and GEO."""
        result = classify_content(
            seo=self.create_seo_analysis(4),
            aeo=self.create_aeo_analysis(8),
            geo=self.create_geo_analysis(8),
        )

        assert result.primary_type == ContentType.AEO_GEO

    def test_only_seo_strong_classified_correctly(self):
        """Test content only strong in SEO."""
        result = classify_content(
            seo=self.create_seo_analysis(8),
            aeo=self.create_aeo_analysis(4),
            geo=self.create_geo_analysis(4),
        )

        assert result.primary_type == ContentType.SEO
        assert result.confidence >= 0.75

    def test_only_aeo_strong_classified_correctly(self):
        """Test content only strong in AEO."""
        result = classify_content(
            seo=self.create_seo_analysis(4),
            aeo=self.create_aeo_analysis(8),
            geo=self.create_geo_analysis(4),
        )

        assert result.primary_type == ContentType.AEO

    def test_only_geo_strong_classified_correctly(self):
        """Test content only strong in GEO."""
        result = classify_content(
            seo=self.create_seo_analysis(4),
            aeo=self.create_aeo_analysis(4),
            geo=self.create_geo_analysis(8),
        )

        assert result.primary_type == ContentType.GEO

    def test_no_strong_areas_uses_highest(self):
        """Test content with no strong areas uses highest score."""
        result = classify_content(
            seo=self.create_seo_analysis(6),
            aeo=self.create_aeo_analysis(4),
            geo=self.create_geo_analysis(5),
        )

        assert result.primary_type == ContentType.SEO
        assert result.confidence < 0.7  # Lower confidence when no strong areas

    def test_explanation_provided(self):
        """Test that explanation is always provided."""
        result = classify_content(
            seo=self.create_seo_analysis(5),
            aeo=self.create_aeo_analysis(5),
            geo=self.create_geo_analysis(5),
        )

        assert result.explanation
        assert len(result.explanation) > 0

    def test_threshold_at_7(self):
        """Test that 7 is the threshold for 'strong'."""
        # Score of 7 should be strong
        strong = classify_content(
            seo=self.create_seo_analysis(7),
            aeo=self.create_aeo_analysis(3),
            geo=self.create_geo_analysis(3),
        )
        assert ContentType.SEO in strong.overlapping_types

        # Score of 6 should not be strong
        not_strong = classify_content(
            seo=self.create_seo_analysis(6),
            aeo=self.create_aeo_analysis(3),
            geo=self.create_geo_analysis(3),
        )
        assert ContentType.SEO not in not_strong.overlapping_types
