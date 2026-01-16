"""SEO analysis service using LLM."""

from typing import Optional

from app.models import KeywordData, PageData, SEOAnalysis
from app.services.llm_client import LLMClient

SEO_SYSTEM_PROMPT = """You are an expert SEO analyst. Analyze the provided webpage content and return a JSON response with your SEO analysis.

Your response must be valid JSON with exactly this structure:
{
    "primary_topic": "The main topic/subject of the content",
    "target_keywords": ["keyword1", "keyword2", "keyword3"],
    "missing_keywords": ["potential keyword 1", "potential keyword 2"],
    "content_gaps": ["gap 1", "gap 2"],
    "cluster_opportunities": ["related topic 1", "related topic 2"],
    "quality_score": 7,
    "quality_rationale": "Explanation of the score",
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]
}

Guidelines:
- target_keywords: Keywords the content is currently optimized for
- missing_keywords: High-value keywords that should be added
- content_gaps: Topics or subtopics that are missing but should be covered
- cluster_opportunities: Related content pieces that could link to this page
- quality_score: 1-10 rating of overall SEO quality
- recommendations: Specific, actionable SEO improvements

If keyword data is provided, prioritize keywords with high volume and low difficulty.
Be specific and actionable in your recommendations."""


def analyze_seo(
    page_data: PageData,
    keyword_data: Optional[list[KeywordData]] = None,
    llm_client: Optional[LLMClient] = None,
) -> SEOAnalysis:
    """
    Perform SEO analysis on page content using LLM.

    Args:
        page_data: The extracted page data to analyze
        keyword_data: Optional keyword data from CSV
        llm_client: Optional LLM client instance

    Returns:
        SEOAnalysis object with findings
    """
    if llm_client is None:
        llm_client = LLMClient()

    # Prepare content for analysis
    content_parts = [
        f"URL: {page_data.url}",
        f"Title: {page_data.title}",
        f"Meta Description: {page_data.meta_description or 'None'}",
        f"Word Count: {page_data.word_count}",
        "",
        "Headings:",
    ]

    for level, headings in page_data.headings.items():
        for heading in headings[:10]:  # Limit headings
            content_parts.append(f"  {level}: {heading}")

    content_parts.extend(["", "Content Summary (first 5 paragraphs):"])
    for para in page_data.paragraphs[:5]:
        # Truncate long paragraphs
        if len(para) > 500:
            para = para[:500] + "..."
        content_parts.append(para)

    # Add keyword data if available
    if keyword_data:
        content_parts.extend(["", "Target Keywords from CSV:"])
        # Sort by volume and take top keywords
        sorted_keywords = sorted(
            [k for k in keyword_data if k.volume],
            key=lambda k: k.volume or 0,
            reverse=True,
        )[:20]
        for kw in sorted_keywords:
            kw_info = f"  - {kw.keyword}"
            if kw.volume:
                kw_info += f" (volume: {kw.volume}"
                if kw.difficulty:
                    kw_info += f", difficulty: {kw.difficulty}"
                kw_info += ")"
            content_parts.append(kw_info)

    content = "\n".join(content_parts)

    # Get LLM analysis
    try:
        result = llm_client.analyze_json(SEO_SYSTEM_PROMPT, content)

        return SEOAnalysis(
            primary_topic=result.get("primary_topic", "Unknown"),
            target_keywords=result.get("target_keywords", []),
            missing_keywords=result.get("missing_keywords", []),
            content_gaps=result.get("content_gaps", []),
            cluster_opportunities=result.get("cluster_opportunities", []),
            quality_score=min(max(result.get("quality_score", 5), 1), 10),
            quality_rationale=result.get("quality_rationale", "Analysis completed"),
            recommendations=result.get("recommendations", []),
        )
    except Exception as e:
        # Return default analysis on error
        return SEOAnalysis(
            primary_topic="Unable to analyze",
            target_keywords=[],
            missing_keywords=[],
            content_gaps=[],
            cluster_opportunities=[],
            quality_score=5,
            quality_rationale=f"Analysis error: {str(e)}",
            recommendations=["Unable to generate recommendations due to analysis error"],
        )
