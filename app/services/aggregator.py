"""Recommendation aggregator service."""

from typing import Optional

from app.models import (
    AEOAnalysis,
    GEOAnalysis,
    KeywordData,
    Recommendation,
    SEOAnalysis,
    Severity,
    StructureAnalysis,
)
from app.services.priority import calculate_priority, estimate_effort, estimate_impact


def aggregate_recommendations(
    structure: StructureAnalysis,
    seo: Optional[SEOAnalysis],
    aeo: Optional[AEOAnalysis],
    geo: Optional[GEOAnalysis],
    keyword_data: Optional[list[KeywordData]] = None,
) -> list[Recommendation]:
    """
    Compile all analyses into prioritized recommendations.

    Args:
        structure: Structure analysis results
        seo: SEO analysis results
        aeo: AEO analysis results
        geo: GEO analysis results
        keyword_data: Optional keyword data from CSV

    Returns:
        Sorted list of recommendations with top priority first
    """
    recommendations: list[Recommendation] = []
    seen_titles: set[str] = set()

    def add_recommendation(
        title: str,
        description: str,
        category: str,
        rationale: str,
        action_items: list[str],
        impact: Optional[str] = None,
        effort: Optional[str] = None,
    ):
        """Helper to add a recommendation if not duplicate."""
        # Simple deduplication by title
        title_key = title.lower().strip()
        if title_key in seen_titles:
            return
        seen_titles.add(title_key)

        # Estimate impact and effort if not provided
        combined_text = f"{title} {description}"
        if not impact:
            impact = estimate_impact(combined_text)
        if not effort:
            effort = estimate_effort(combined_text)

        priority = calculate_priority(
            title=title,
            category=category,
            impact=impact,
            effort=effort,
            keyword_data=keyword_data,
        )

        recommendations.append(
            Recommendation(
                title=title,
                description=description,
                category=category,
                priority=priority,
                rationale=rationale,
                action_items=action_items,
            )
        )

    # Add structural issues
    severity_impact = {
        Severity.CRITICAL: "high",
        Severity.HIGH: "high",
        Severity.MEDIUM: "medium",
        Severity.LOW: "low",
    }

    for issue in structure.issues:
        add_recommendation(
            title=f"Fix: {issue.issue}",
            description=issue.recommendation,
            category="Structure",
            rationale="Structural issues directly impact crawlability and user experience",
            action_items=[issue.recommendation],
            impact=severity_impact.get(issue.severity, "medium"),
            effort="low",
        )

    # Add SEO recommendations
    if seo:
        for rec in seo.recommendations:
            add_recommendation(
                title=rec if len(rec) < 60 else rec[:57] + "...",
                description=rec,
                category="SEO",
                rationale=seo.quality_rationale,
                action_items=[rec],
            )

        # Add missing keywords as recommendations
        if seo.missing_keywords:
            keywords_str = ", ".join(seo.missing_keywords[:5])
            add_recommendation(
                title="Target missing keywords",
                description=f"Consider targeting these keywords: {keywords_str}",
                category="SEO",
                rationale="These keywords are relevant but not currently optimized",
                action_items=[
                    f"Research and incorporate '{kw}' into content"
                    for kw in seo.missing_keywords[:3]
                ],
            )

        # Add content gaps
        for gap in seo.content_gaps[:3]:
            add_recommendation(
                title=f"Address content gap: {gap[:50]}",
                description=f"The content is missing coverage of: {gap}",
                category="SEO",
                rationale="Filling content gaps improves topical authority",
                action_items=[f"Add section or content addressing: {gap}"],
            )

    # Add AEO recommendations
    if aeo:
        for rec in aeo.recommendations:
            add_recommendation(
                title=rec if len(rec) < 60 else rec[:57] + "...",
                description=rec,
                category="AEO",
                rationale=aeo.readiness_rationale,
                action_items=[rec],
            )

        # Add PAA opportunities
        if aeo.paa_opportunities:
            paa_str = "; ".join(aeo.paa_opportunities[:3])
            add_recommendation(
                title="Target People Also Ask questions",
                description=f"Consider addressing these questions: {paa_str}",
                category="AEO",
                rationale="PAA questions have high visibility in search results",
                action_items=[
                    f"Add section answering: '{q}'" for q in aeo.paa_opportunities[:3]
                ],
            )

        # Add questions to address
        if aeo.questions_to_add:
            add_recommendation(
                title="Answer additional user questions",
                description="Add content that directly answers common user questions",
                category="AEO",
                rationale="Question-focused content performs well in answer engines",
                action_items=[
                    f"Add answer for: '{q}'" for q in aeo.questions_to_add[:3]
                ],
            )

    # Add GEO recommendations
    if geo:
        for rec in geo.recommendations:
            add_recommendation(
                title=rec if len(rec) < 60 else rec[:57] + "...",
                description=rec,
                category="GEO",
                rationale=geo.strength_rationale,
                action_items=[rec],
            )

        # Add defensibility suggestions
        for suggestion in geo.defensibility_suggestions[:2]:
            add_recommendation(
                title=f"Improve defensibility: {suggestion[:40]}",
                description=suggestion,
                category="GEO",
                rationale="Making content more unique protects against AI absorption",
                action_items=[suggestion],
            )

        # Flag absorption risks
        if geo.absorption_risks:
            risks_str = "; ".join(geo.absorption_risks[:3])
            add_recommendation(
                title="Address content absorption risks",
                description=f"This content may be absorbed by AI without citation: {risks_str}",
                category="GEO",
                rationale="Generic content risks losing attribution in AI-generated responses",
                action_items=[
                    "Add unique data, frameworks, or expert insights",
                    "Include proprietary information not available elsewhere",
                    "Strengthen brand voice and perspective",
                ],
                impact="high",
            )

    # Sort by priority score (highest first)
    recommendations.sort(key=lambda r: r.priority.score, reverse=True)

    return recommendations
