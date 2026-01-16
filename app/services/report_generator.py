"""Report generation services for Markdown, HTML, and CSV output."""

import csv
import io

import markdown

from app.models import AnalysisResult, PageAnalysisResult


def generate_markdown_report(result: AnalysisResult) -> str:
    """
    Generate a Markdown report from analysis results.

    Args:
        result: The complete analysis result

    Returns:
        Markdown formatted report string
    """
    lines = []

    # Header
    lines.append("# SEO/AEO/GEO Analysis Report")
    lines.append("")
    lines.append(f"**URL:** {result.url}")
    lines.append(f"**Date:** {result.timestamp.strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"**Mode:** {'Full Site' if result.mode.value == 'full' else 'Single Page'}")
    lines.append(f"**Pages Analyzed:** {len(result.pages)}")
    lines.append("")

    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append("### Overall Scores")
    lines.append("")
    lines.append("| Dimension | Score | Rating |")
    lines.append("|-----------|-------|--------|")
    lines.append(
        f"| SEO | {result.overall_seo_score}/10 | {_score_rating(result.overall_seo_score)} |"
    )
    lines.append(
        f"| AEO | {result.overall_aeo_score}/10 | {_score_rating(result.overall_aeo_score)} |"
    )
    lines.append(
        f"| GEO | {result.overall_geo_score}/10 | {_score_rating(result.overall_geo_score)} |"
    )
    lines.append("")

    # Top Recommendations
    top_recs = result.recommendations[:10]
    if top_recs:
        lines.append("### Top 10 Priority Recommendations")
        lines.append("")
        for i, rec in enumerate(top_recs, 1):
            lines.append(f"{i}. **{rec.title}** (Priority: {rec.priority.score}/100)")
            lines.append(f"   - {rec.description}")
            lines.append(f"   - Category: {rec.category} | Impact: {rec.priority.impact} | Effort: {rec.priority.effort}")
            lines.append("")

    # Page-by-Page Analysis
    if len(result.pages) > 1:
        lines.append("## Page-by-Page Analysis")
        lines.append("")

    for page_result in result.pages:
        lines.extend(_generate_page_section(page_result, len(result.pages) > 1))

    # SEO Findings
    lines.append("## SEO Findings")
    lines.append("")

    for page_result in result.pages:
        if page_result.seo:
            seo = page_result.seo
            if len(result.pages) > 1:
                lines.append(f"### {page_result.page_data.url}")
                lines.append("")

            lines.append(f"**Primary Topic:** {seo.primary_topic}")
            lines.append(f"**Quality Score:** {seo.quality_score}/10")
            lines.append(f"**Rationale:** {seo.quality_rationale}")
            lines.append("")

            if seo.target_keywords:
                lines.append("**Current Target Keywords:**")
                for kw in seo.target_keywords:
                    lines.append(f"- {kw}")
                lines.append("")

            if seo.missing_keywords:
                lines.append("**Keyword Opportunities:**")
                for kw in seo.missing_keywords:
                    lines.append(f"- {kw}")
                lines.append("")

            if seo.content_gaps:
                lines.append("**Content Gaps:**")
                for gap in seo.content_gaps:
                    lines.append(f"- {gap}")
                lines.append("")

            if seo.cluster_opportunities:
                lines.append("**Cluster Opportunities:**")
                for cluster in seo.cluster_opportunities:
                    lines.append(f"- {cluster}")
                lines.append("")

    # AEO Findings
    lines.append("## AEO Findings")
    lines.append("")

    for page_result in result.pages:
        if page_result.aeo:
            aeo = page_result.aeo
            if len(result.pages) > 1:
                lines.append(f"### {page_result.page_data.url}")
                lines.append("")

            lines.append(f"**Readiness Score:** {aeo.readiness_score}/10")
            lines.append(f"**Rationale:** {aeo.readiness_rationale}")
            lines.append(f"**Format Quality:** {aeo.format_quality}")
            lines.append(f"**Featured Snippet Potential:** {aeo.featured_snippet_potential}")
            lines.append("")

            if aeo.questions_answered:
                lines.append("**Questions Answered:**")
                for q in aeo.questions_answered:
                    lines.append(f"- {q}")
                lines.append("")

            if aeo.questions_to_add:
                lines.append("**Questions to Add:**")
                for q in aeo.questions_to_add:
                    lines.append(f"- {q}")
                lines.append("")

            if aeo.paa_opportunities:
                lines.append("**People Also Ask Opportunities:**")
                for q in aeo.paa_opportunities:
                    lines.append(f"- {q}")
                lines.append("")

    # GEO Findings
    lines.append("## GEO Findings")
    lines.append("")

    for page_result in result.pages:
        if page_result.geo:
            geo = page_result.geo
            if len(result.pages) > 1:
                lines.append(f"### {page_result.page_data.url}")
                lines.append("")

            lines.append(f"**Strength Score:** {geo.strength_score}/10")
            lines.append(f"**Rationale:** {geo.strength_rationale}")
            lines.append(f"**Originality Assessment:** {geo.originality_assessment}")
            lines.append("")

            if geo.citation_worthy_elements:
                lines.append("**Citation-Worthy Elements:**")
                for elem in geo.citation_worthy_elements:
                    lines.append(f"- {elem}")
                lines.append("")

            if geo.absorption_risks:
                lines.append("**Absorption Risks:**")
                for risk in geo.absorption_risks:
                    lines.append(f"- {risk}")
                lines.append("")

            if geo.defensibility_suggestions:
                lines.append("**Defensibility Suggestions:**")
                for sugg in geo.defensibility_suggestions:
                    lines.append(f"- {sugg}")
                lines.append("")

    # Structural Issues
    lines.append("## Structural Issues")
    lines.append("")

    has_issues = False
    for page_result in result.pages:
        if page_result.structure.issues:
            has_issues = True
            if len(result.pages) > 1:
                lines.append(f"### {page_result.page_data.url}")
                lines.append("")

            for issue in page_result.structure.issues:
                lines.append(f"- **{issue.issue}** ({issue.severity.value})")
                lines.append(f"  - {issue.recommendation}")
            lines.append("")

    if not has_issues:
        lines.append("No significant structural issues found.")
        lines.append("")

    # All Recommendations
    if result.recommendations:
        lines.append("## All Recommendations")
        lines.append("")

        # Group by category
        categories = {}
        for rec in result.recommendations:
            if rec.category not in categories:
                categories[rec.category] = []
            categories[rec.category].append(rec)

        for category, recs in categories.items():
            lines.append(f"### {category}")
            lines.append("")
            for rec in recs:
                lines.append(f"- **{rec.title}** (Priority: {rec.priority.score})")
                if rec.action_items:
                    for action in rec.action_items[:2]:
                        lines.append(f"  - {action}")
            lines.append("")

    return "\n".join(lines)


def _generate_page_section(page_result: PageAnalysisResult, show_url: bool) -> list[str]:
    """Generate markdown section for a single page."""
    lines = []
    page = page_result.page_data

    if show_url:
        lines.append(f"### {page.url}")
    else:
        lines.append("### Page Overview")
    lines.append("")

    lines.append(f"- **Title:** {page.title or 'None'}")
    lines.append(f"- **Word Count:** {page.word_count}")
    lines.append(f"- **Has FAQ Section:** {'Yes' if page.has_faq_section else 'No'}")
    lines.append(f"- **Has Schema Markup:** {'Yes' if page.has_schema_markup else 'No'}")

    if page_result.classification:
        lines.append(
            f"- **Content Type:** {page_result.classification.primary_type.value.upper()}"
        )
        lines.append(
            f"- **Classification Confidence:** {page_result.classification.confidence:.0%}"
        )

    lines.append("")
    return lines


def _score_rating(score: int) -> str:
    """Convert numeric score to rating text."""
    if score >= 8:
        return "Excellent"
    elif score >= 6:
        return "Good"
    elif score >= 4:
        return "Fair"
    else:
        return "Needs Work"


def generate_html_report(result: AnalysisResult) -> str:
    """
    Generate an HTML report from analysis results.

    Args:
        result: The complete analysis result

    Returns:
        HTML formatted report string
    """
    md_content = generate_markdown_report(result)
    html_content = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

    # Wrap in styled HTML
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SEO Analysis Report - {result.url}</title>
    <style>
        :root {{
            --color-primary: #2563eb;
            --color-success: #16a34a;
            --color-warning: #ca8a04;
            --color-danger: #dc2626;
            --color-bg: #f8fafc;
            --color-text: #1e293b;
            --color-border: #e2e8f0;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
            background: var(--color-bg);
            color: var(--color-text);
        }}
        h1 {{ color: var(--color-primary); border-bottom: 2px solid var(--color-primary); padding-bottom: 0.5rem; }}
        h2 {{ color: var(--color-primary); margin-top: 2rem; border-bottom: 1px solid var(--color-border); padding-bottom: 0.25rem; }}
        h3 {{ margin-top: 1.5rem; }}
        table {{ border-collapse: collapse; width: 100%; margin: 1rem 0; }}
        th, td {{ border: 1px solid var(--color-border); padding: 0.75rem; text-align: left; }}
        th {{ background: var(--color-bg); font-weight: 600; }}
        ul, ol {{ margin: 0.75rem 0; padding-left: 1.5rem; }}
        li {{ margin: 0.5rem 0; }}
        strong {{ color: var(--color-text); }}
        code {{ background: #e2e8f0; padding: 0.125rem 0.375rem; border-radius: 4px; font-size: 0.9em; }}
        .score-excellent {{ color: var(--color-success); font-weight: bold; }}
        .score-good {{ color: var(--color-success); }}
        .score-fair {{ color: var(--color-warning); }}
        .score-poor {{ color: var(--color-danger); }}
        @media print {{
            body {{ padding: 0; }}
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""


def generate_csv_export(result: AnalysisResult) -> str:
    """
    Generate a CSV export of keywords and questions.

    Args:
        result: The complete analysis result

    Returns:
        CSV formatted string
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(["Item", "Type", "Source", "Priority", "Notes"])

    # Collect all items
    for page_result in result.pages:
        page_url = page_result.page_data.url

        # SEO keywords
        if page_result.seo:
            for kw in page_result.seo.target_keywords:
                writer.writerow([kw, "keyword", "SEO (current)", "", f"From: {page_url}"])

            for kw in page_result.seo.missing_keywords:
                writer.writerow([kw, "keyword", "SEO (opportunity)", "High", f"From: {page_url}"])

        # AEO questions
        if page_result.aeo:
            for q in page_result.aeo.questions_answered:
                writer.writerow([q, "question", "AEO (answered)", "", f"From: {page_url}"])

            for q in page_result.aeo.questions_to_add:
                writer.writerow([q, "question", "AEO (opportunity)", "High", f"From: {page_url}"])

            for q in page_result.aeo.paa_opportunities:
                writer.writerow([q, "question", "AEO (PAA)", "High", f"From: {page_url}"])

        # GEO elements
        if page_result.geo:
            for elem in page_result.geo.citation_worthy_elements:
                writer.writerow([elem, "element", "GEO (citation-worthy)", "", f"From: {page_url}"])

    # Add imported keywords if available
    if result.keywords_used:
        for kw in result.keywords_used:
            notes = []
            if kw.volume:
                notes.append(f"Volume: {kw.volume}")
            if kw.difficulty:
                notes.append(f"KD: {kw.difficulty}")
            if kw.cpc:
                notes.append(f"CPC: ${kw.cpc}")

            writer.writerow([
                kw.keyword,
                "keyword",
                "Imported (CSV)",
                "",
                "; ".join(notes) if notes else "",
            ])

    return output.getvalue()
