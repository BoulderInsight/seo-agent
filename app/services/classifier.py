"""Content classification service."""

from app.models import (
    AEOAnalysis,
    ContentClassification,
    ContentType,
    GEOAnalysis,
    SEOAnalysis,
)


def classify_content(
    seo: SEOAnalysis,
    aeo: AEOAnalysis,
    geo: GEOAnalysis,
) -> ContentClassification:
    """
    Classify content based on SEO, AEO, and GEO analysis scores.

    Args:
        seo: SEO analysis results
        aeo: AEO analysis results
        geo: GEO analysis results

    Returns:
        ContentClassification with primary type and overlaps
    """
    seo_score = seo.quality_score
    aeo_score = aeo.readiness_score
    geo_score = geo.strength_score

    # Determine strong categories (score >= 7)
    strong_seo = seo_score >= 7
    strong_aeo = aeo_score >= 7
    strong_geo = geo_score >= 7

    # Determine which types the content serves
    overlapping: list[ContentType] = []

    if strong_seo:
        overlapping.append(ContentType.SEO)
    if strong_aeo:
        overlapping.append(ContentType.AEO)
    if strong_geo:
        overlapping.append(ContentType.GEO)

    # Determine primary type based on highest score and overlaps
    if strong_seo and strong_aeo and strong_geo:
        primary = ContentType.ALL
        confidence = 0.9
        explanation = (
            "Content excels across all three optimization dimensions. "
            "It's well-optimized for search engines, answer engines, and generative AI."
        )
    elif strong_seo and strong_aeo:
        primary = ContentType.SEO_AEO
        confidence = 0.85
        explanation = (
            "Content is strong for both traditional search and answer engines. "
            "Consider strengthening unique, citation-worthy elements for GEO."
        )
    elif strong_seo and strong_geo:
        primary = ContentType.SEO_GEO
        confidence = 0.85
        explanation = (
            "Content ranks well and has defensible, unique elements. "
            "Consider adding more question-focused content for AEO."
        )
    elif strong_aeo and strong_geo:
        primary = ContentType.AEO_GEO
        confidence = 0.85
        explanation = (
            "Content answers questions well and is citation-worthy. "
            "Consider traditional SEO improvements for broader reach."
        )
    elif strong_seo:
        primary = ContentType.SEO
        confidence = 0.8
        explanation = (
            "Content is primarily optimized for traditional search engines. "
            "Consider adding question-based content and unique insights."
        )
    elif strong_aeo:
        primary = ContentType.AEO
        confidence = 0.8
        explanation = (
            "Content is well-suited for answer engines and featured snippets. "
            "Consider SEO fundamentals and adding proprietary elements."
        )
    elif strong_geo:
        primary = ContentType.GEO
        confidence = 0.8
        explanation = (
            "Content has strong unique/proprietary elements. "
            "Consider improving discoverability through SEO and AEO."
        )
    else:
        # No strong category - determine primary by highest score
        scores = {"SEO": seo_score, "AEO": aeo_score, "GEO": geo_score}
        highest = max(scores, key=scores.get)

        primary = ContentType[highest]
        confidence = 0.6
        explanation = (
            f"Content has room for improvement across all dimensions. "
            f"Currently strongest in {highest} (score: {scores[highest]}/10). "
            f"Focus on improving the weakest areas for better overall performance."
        )

    return ContentClassification(
        primary_type=primary,
        confidence=confidence,
        explanation=explanation,
        overlapping_types=overlapping,
    )
