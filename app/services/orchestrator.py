"""Analysis orchestrator service."""

import uuid
from datetime import datetime
from typing import Callable, Optional

from app.models import (
    AnalysisMode,
    AnalysisResult,
    KeywordData,
    PageAnalysisResult,
)
from app.services.aeo_analyzer import analyze_aeo
from app.services.aggregator import aggregate_recommendations
from app.services.classifier import classify_content
from app.services.crawler import crawl_page, crawl_site
from app.services.geo_analyzer import analyze_geo
from app.services.llm_client import LLMClient
from app.services.seo_analyzer import analyze_seo
from app.services.structure_analyzer import analyze_structure


def run_analysis(
    url: str,
    mode: AnalysisMode,
    max_pages: int = 10,
    keyword_data: Optional[list[KeywordData]] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None,
) -> AnalysisResult:
    """
    Run complete analysis workflow on a URL.

    Args:
        url: The URL to analyze
        mode: Single page or full site mode
        max_pages: Maximum pages to crawl in full site mode
        keyword_data: Optional keyword data from CSV
        progress_callback: Optional callback for progress updates

    Returns:
        Complete AnalysisResult with all analyses
    """

    def update_progress(step: str, percent: int):
        if progress_callback:
            progress_callback(step, percent)

    # Initialize
    update_progress("Starting analysis...", 0)
    analysis_id = str(uuid.uuid4())

    # Step 1: Crawl
    update_progress("Crawling pages...", 5)

    if mode == AnalysisMode.SINGLE_PAGE:
        pages_data = [crawl_page(url)]
    else:
        pages_data = crawl_site(url, max_pages, progress_callback)

    # Check for crawl errors
    successful_pages = [p for p in pages_data if not p.error]
    if not successful_pages:
        error_msg = pages_data[0].error if pages_data else "Failed to crawl URL"
        return AnalysisResult(
            id=analysis_id,
            url=url,
            mode=mode,
            timestamp=datetime.now(),
            pages=[],
            recommendations=[],
            error=error_msg,
        )

    # Initialize LLM client once
    update_progress("Initializing AI analysis...", 30)
    try:
        llm_client = LLMClient()
    except Exception as e:
        return AnalysisResult(
            id=analysis_id,
            url=url,
            mode=mode,
            timestamp=datetime.now(),
            pages=[],
            recommendations=[],
            error=f"Failed to initialize LLM client: {e}",
        )

    # Step 2: Analyze each page
    page_results: list[PageAnalysisResult] = []
    total_pages = len(successful_pages)

    for i, page_data in enumerate(successful_pages):
        page_num = i + 1
        progress_base = 30 + int((i / total_pages) * 50)

        # Structure analysis
        update_progress(f"Analyzing structure ({page_num}/{total_pages})...", progress_base)
        structure = analyze_structure(page_data)

        # Skip LLM analysis for pages with errors or very thin content
        if page_data.word_count < 50:
            page_results.append(
                PageAnalysisResult(
                    page_data=page_data,
                    structure=structure,
                )
            )
            continue

        # SEO analysis
        update_progress(f"SEO analysis ({page_num}/{total_pages})...", progress_base + 5)
        try:
            seo = analyze_seo(page_data, keyword_data, llm_client)
        except Exception:
            seo = None

        # AEO analysis
        update_progress(f"AEO analysis ({page_num}/{total_pages})...", progress_base + 10)
        try:
            aeo = analyze_aeo(page_data, llm_client)
        except Exception:
            aeo = None

        # GEO analysis
        update_progress(f"GEO analysis ({page_num}/{total_pages})...", progress_base + 15)
        try:
            geo = analyze_geo(page_data, llm_client)
        except Exception:
            geo = None

        # Classification
        classification = None
        if seo and aeo and geo:
            classification = classify_content(seo, aeo, geo)

        page_results.append(
            PageAnalysisResult(
                page_data=page_data,
                structure=structure,
                seo=seo,
                aeo=aeo,
                geo=geo,
                classification=classification,
            )
        )

    # Step 3: Aggregate recommendations
    update_progress("Generating recommendations...", 85)

    all_recommendations = []
    for page_result in page_results:
        recs = aggregate_recommendations(
            structure=page_result.structure,
            seo=page_result.seo,
            aeo=page_result.aeo,
            geo=page_result.geo,
            keyword_data=keyword_data,
        )
        all_recommendations.extend(recs)

    # Deduplicate and sort recommendations across all pages
    seen_titles = set()
    unique_recommendations = []
    for rec in sorted(all_recommendations, key=lambda r: r.priority.score, reverse=True):
        if rec.title.lower() not in seen_titles:
            seen_titles.add(rec.title.lower())
            unique_recommendations.append(rec)

    # Calculate overall scores
    update_progress("Finalizing report...", 95)

    seo_scores = [p.seo.quality_score for p in page_results if p.seo]
    aeo_scores = [p.aeo.readiness_score for p in page_results if p.aeo]
    geo_scores = [p.geo.strength_score for p in page_results if p.geo]

    overall_seo = round(sum(seo_scores) / len(seo_scores)) if seo_scores else 0
    overall_aeo = round(sum(aeo_scores) / len(aeo_scores)) if aeo_scores else 0
    overall_geo = round(sum(geo_scores) / len(geo_scores)) if geo_scores else 0

    update_progress("Complete!", 100)

    return AnalysisResult(
        id=analysis_id,
        url=url,
        mode=mode,
        timestamp=datetime.now(),
        pages=page_results,
        recommendations=unique_recommendations,
        overall_seo_score=overall_seo,
        overall_aeo_score=overall_aeo,
        overall_geo_score=overall_geo,
        keywords_used=keyword_data or [],
    )
