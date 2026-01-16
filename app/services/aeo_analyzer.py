"""AEO (Answer Engine Optimization) analysis service using LLM."""

from typing import Optional

from app.models import AEOAnalysis, PageData
from app.services.llm_client import LLMClient

AEO_SYSTEM_PROMPT = """You are an expert in Answer Engine Optimization (AEO). Analyze the provided webpage content for its effectiveness in answering user questions and appearing in AI-powered answer engines.

Your response must be valid JSON with exactly this structure:
{
    "questions_answered": ["What question does this content answer?", "Another question answered"],
    "questions_to_add": ["Question the content should answer", "Another missing question"],
    "paa_opportunities": ["People Also Ask question 1", "People Also Ask question 2"],
    "featured_snippet_potential": "Description of featured snippet opportunities",
    "format_quality": "Assessment of how well-formatted the content is for answer extraction",
    "readiness_score": 7,
    "readiness_rationale": "Explanation of the AEO readiness score",
    "recommendations": ["recommendation 1", "recommendation 2", "recommendation 3"]
}

Guidelines:
- questions_answered: Questions that the current content directly answers
- questions_to_add: Questions users might ask that aren't addressed
- paa_opportunities: "People Also Ask" style questions to target
- featured_snippet_potential: Analysis of which content could win featured snippets
- format_quality: Evaluate conciseness, directness, structure (lists, tables, etc.)
- readiness_score: 1-10 rating of how ready the content is for answer engines
- recommendations: Specific improvements for AEO

Focus on:
- Direct, concise answers in the first paragraph
- Question-formatted headings (H2s/H3s as questions)
- List and table formatting for easy extraction
- Clear definitions and explanations
- FAQ sections and structured Q&A content"""


def analyze_aeo(
    page_data: PageData,
    llm_client: Optional[LLMClient] = None,
) -> AEOAnalysis:
    """
    Perform AEO analysis on page content using LLM.

    Args:
        page_data: The extracted page data to analyze
        llm_client: Optional LLM client instance

    Returns:
        AEOAnalysis object with findings
    """
    if llm_client is None:
        llm_client = LLMClient()

    # Prepare content for analysis
    content_parts = [
        f"URL: {page_data.url}",
        f"Title: {page_data.title}",
        f"Meta Description: {page_data.meta_description or 'None'}",
        f"Has FAQ Section: {page_data.has_faq_section}",
        f"Has TLDR/Summary: {page_data.has_tldr_section}",
        f"Word Count: {page_data.word_count}",
        "",
        "Headings:",
    ]

    for level, headings in page_data.headings.items():
        for heading in headings[:15]:
            content_parts.append(f"  {level}: {heading}")

    content_parts.extend(["", "Content (first 8 paragraphs):"])
    for para in page_data.paragraphs[:8]:
        if len(para) > 400:
            para = para[:400] + "..."
        content_parts.append(para)

    content = "\n".join(content_parts)

    # Get LLM analysis
    try:
        result = llm_client.analyze_json(AEO_SYSTEM_PROMPT, content)

        return AEOAnalysis(
            questions_answered=result.get("questions_answered", []),
            questions_to_add=result.get("questions_to_add", []),
            paa_opportunities=result.get("paa_opportunities", []),
            featured_snippet_potential=result.get(
                "featured_snippet_potential", "No specific opportunities identified"
            ),
            format_quality=result.get("format_quality", "Not assessed"),
            readiness_score=min(max(result.get("readiness_score", 5), 1), 10),
            readiness_rationale=result.get("readiness_rationale", "Analysis completed"),
            recommendations=result.get("recommendations", []),
        )
    except Exception as e:
        return AEOAnalysis(
            questions_answered=[],
            questions_to_add=[],
            paa_opportunities=[],
            featured_snippet_potential="Unable to analyze",
            format_quality="Unable to analyze",
            readiness_score=5,
            readiness_rationale=f"Analysis error: {str(e)}",
            recommendations=["Unable to generate recommendations due to analysis error"],
        )
