"""GEO (Generative Engine Optimization) analysis service using LLM."""

from typing import Optional

from app.models import GEOAnalysis, PageData
from app.services.llm_client import LLMClient

GEO_SYSTEM_PROMPT = """You are an expert in Generative Engine Optimization (GEO). Analyze the provided webpage content for its defensibility against LLM absorption and citation-worthiness in AI-generated responses.

Your response must be valid JSON with exactly this structure:
{
    "originality_assessment": "Assessment of content originality (generic vs proprietary)",
    "citation_worthy_elements": ["element 1", "element 2"],
    "absorption_risks": ["risk 1", "risk 2"],
    "defensibility_suggestions": ["suggestion 1", "suggestion 2"],
    "strength_score": 7,
    "strength_rationale": "Explanation of the GEO strength score",
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]
}

Guidelines:
- originality_assessment: Is content generic (easily replicated by AI) or unique/proprietary?
- citation_worthy_elements: What makes this content worth citing? (original research, unique data, frameworks, expert insights, case studies)
- absorption_risks: Content that AI could absorb without attribution (generic advice, common knowledge)
- defensibility_suggestions: How to make content more unique and citation-worthy
- strength_score: 1-10 rating of GEO defensibility
- recommendations: Specific improvements for GEO

Content that is GEO-strong typically has:
- Original research, data, or statistics
- Unique frameworks, methodologies, or models
- Expert opinions with clear attribution
- Case studies with specific details
- Proprietary insights not available elsewhere
- Strong brand voice and perspective

Content at risk of absorption:
- Generic how-to guides
- Common knowledge explanations
- Unattributed statistics
- Advice without unique perspective
- Content that reads like AI-generated text"""


def analyze_geo(
    page_data: PageData,
    llm_client: Optional[LLMClient] = None,
) -> GEOAnalysis:
    """
    Perform GEO analysis on page content using LLM.

    Args:
        page_data: The extracted page data to analyze
        llm_client: Optional LLM client instance

    Returns:
        GEOAnalysis object with findings
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
        for heading in headings[:15]:
            content_parts.append(f"  {level}: {heading}")

    content_parts.extend(["", "Full Content (first 10 paragraphs):"])
    for para in page_data.paragraphs[:10]:
        if len(para) > 500:
            para = para[:500] + "..."
        content_parts.append(para)

    content = "\n".join(content_parts)

    # Get LLM analysis
    try:
        result = llm_client.analyze_json(GEO_SYSTEM_PROMPT, content)

        return GEOAnalysis(
            originality_assessment=result.get(
                "originality_assessment", "Unable to assess"
            ),
            citation_worthy_elements=result.get("citation_worthy_elements", []),
            absorption_risks=result.get("absorption_risks", []),
            defensibility_suggestions=result.get("defensibility_suggestions", []),
            strength_score=min(max(result.get("strength_score", 5), 1), 10),
            strength_rationale=result.get("strength_rationale", "Analysis completed"),
            recommendations=result.get("recommendations", []),
        )
    except Exception as e:
        return GEOAnalysis(
            originality_assessment="Unable to analyze",
            citation_worthy_elements=[],
            absorption_risks=[],
            defensibility_suggestions=[],
            strength_score=5,
            strength_rationale=f"Analysis error: {str(e)}",
            recommendations=["Unable to generate recommendations due to analysis error"],
        )
