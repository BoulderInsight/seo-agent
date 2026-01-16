"""Priority scoring service for recommendations."""

from typing import Optional

from app.models import KeywordData, PriorityScore


def calculate_priority(
    title: str,
    category: str,
    impact: str,
    effort: str,
    keyword_data: Optional[list[KeywordData]] = None,
) -> PriorityScore:
    """
    Calculate priority score for a recommendation.

    Args:
        title: The recommendation title
        category: Category (SEO, AEO, GEO, Structure)
        impact: Potential impact (high, medium, low)
        effort: Implementation effort (high, medium, low)
        keyword_data: Optional keyword data for volume consideration

    Returns:
        PriorityScore with calculated score and factors
    """
    factors: dict[str, int] = {}

    # Impact score (0-40)
    impact_scores = {"high": 40, "medium": 25, "low": 10}
    impact_score = impact_scores.get(impact.lower(), 20)
    factors["impact"] = impact_score

    # Effort score (inverted: low effort = high score) (0-30)
    effort_scores = {"low": 30, "medium": 20, "high": 10}
    effort_score = effort_scores.get(effort.lower(), 15)
    factors["effort"] = effort_score

    # Category weight (0-15)
    # Structure issues often have the highest ROI
    category_scores = {
        "structure": 15,
        "seo": 12,
        "aeo": 10,
        "geo": 8,
    }
    category_score = category_scores.get(category.lower(), 10)
    factors["category"] = category_score

    # Keyword volume bonus (0-15)
    keyword_volume = 0
    max_volume = None
    if keyword_data:
        # Find if any keywords relate to this recommendation
        title_lower = title.lower()
        for kw in keyword_data:
            if kw.keyword.lower() in title_lower or any(
                word in title_lower for word in kw.keyword.lower().split()
            ):
                if kw.volume and (max_volume is None or kw.volume > max_volume):
                    max_volume = kw.volume

        if max_volume:
            if max_volume >= 10000:
                keyword_volume = 15
            elif max_volume >= 1000:
                keyword_volume = 10
            elif max_volume >= 100:
                keyword_volume = 5
            else:
                keyword_volume = 2

    factors["keyword_volume"] = keyword_volume

    # Calculate total score (1-100)
    total = sum(factors.values())
    total = min(max(total, 1), 100)

    return PriorityScore(
        score=total,
        impact=impact,
        effort=effort,
        keyword_volume=max_volume,
        factors=factors,
    )


def estimate_impact(issue_or_rec: str) -> str:
    """Estimate impact level based on the recommendation text."""
    high_indicators = [
        "missing h1",
        "missing meta",
        "no title",
        "thin content",
        "missing keyword",
        "critical",
        "high priority",
        "primary",
    ]
    low_indicators = [
        "consider",
        "optional",
        "minor",
        "slightly",
        "could",
        "might",
    ]

    text_lower = issue_or_rec.lower()

    if any(ind in text_lower for ind in high_indicators):
        return "high"
    elif any(ind in text_lower for ind in low_indicators):
        return "low"
    return "medium"


def estimate_effort(issue_or_rec: str) -> str:
    """Estimate effort level based on the recommendation text."""
    low_effort = [
        "add",
        "update",
        "change",
        "fix",
        "modify",
        "meta",
        "title",
        "heading",
    ]
    high_effort = [
        "restructure",
        "rewrite",
        "create new",
        "research",
        "develop",
        "comprehensive",
        "multiple pages",
    ]

    text_lower = issue_or_rec.lower()

    if any(ind in text_lower for ind in high_effort):
        return "high"
    elif any(ind in text_lower for ind in low_effort):
        return "low"
    return "medium"
