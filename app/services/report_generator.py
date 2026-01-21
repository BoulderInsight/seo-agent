"""Report generation services for Markdown, HTML, CSV, and PDF output."""

import base64
import csv
import io
import os
from io import BytesIO
from pathlib import Path

import markdown

from app.models import AnalysisResult, PageAnalysisResult


def _get_logo_base64() -> str:
    """Get the EngineOp logo as a base64-encoded data URI."""
    # Find the logo file
    app_dir = Path(__file__).parent.parent
    logo_path = app_dir / "static" / "images" / "EngineOpDark.png"

    if not logo_path.exists():
        # Fallback to root directory
        logo_path = app_dir.parent / "EngineOpDark.png"

    if logo_path.exists():
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{logo_data}"

    return ""


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


def generate_pdf_report(result: AnalysisResult) -> bytes:
    """
    Generate a styled PDF report from analysis results.

    Args:
        result: The complete analysis result

    Returns:
        PDF file as bytes
    """
    from weasyprint import HTML, CSS

    # Build the HTML content for PDF
    html_content = _build_pdf_html(result)

    # Convert to PDF
    html_doc = HTML(string=html_content)
    pdf_bytes = html_doc.write_pdf()

    return pdf_bytes


def _build_pdf_html(result: AnalysisResult) -> str:
    """Build styled HTML for PDF generation with executive-ready layout."""

    logo_data_uri = _get_logo_base64()

    def score_color(score: int) -> str:
        if score >= 8:
            return "#059669"
        elif score >= 6:
            return "#0891b2"
        elif score >= 4:
            return "#d97706"
        return "#dc2626"

    def score_bg(score: int) -> str:
        if score >= 8:
            return "#ecfdf5"
        elif score >= 6:
            return "#ecfeff"
        elif score >= 4:
            return "#fffbeb"
        return "#fef2f2"

    seo_score = result.overall_seo_score
    aeo_score = result.overall_aeo_score
    geo_score = result.overall_geo_score

    # Gather recommendations by category
    seo_recs = [r for r in result.recommendations if r.category == "SEO"]
    aeo_recs = [r for r in result.recommendations if r.category in ("AEO", "Structure")]
    geo_recs = [r for r in result.recommendations if r.category == "GEO"]
    all_recs = result.recommendations

    # Get top 3 priorities for executive summary
    top_priorities = all_recs[:3] if all_recs else []

    # Collect SEO data
    seo_current_keywords = []
    seo_missing_keywords = []
    seo_content_gaps = []
    seo_primary_topic = ""
    seo_rationale = ""

    # Collect AEO data
    aeo_rationale = ""
    aeo_snippet_potential = ""
    aeo_questions_answered = []
    aeo_questions_to_add = []
    aeo_paa = []

    # Collect GEO data
    geo_originality = ""
    geo_rationale = ""
    geo_citations = []
    geo_risks = []
    geo_suggestions = []

    # Collect structural issues
    structural_issues = []

    for page_result in result.pages:
        if page_result.seo:
            seo = page_result.seo
            seo_primary_topic = seo.primary_topic or seo_primary_topic
            seo_rationale = seo.quality_rationale or seo_rationale
            seo_current_keywords.extend(seo.target_keywords or [])
            seo_missing_keywords.extend(seo.missing_keywords or [])
            seo_content_gaps.extend(seo.content_gaps or [])

        if page_result.aeo:
            aeo = page_result.aeo
            aeo_rationale = aeo.readiness_rationale or aeo_rationale
            aeo_snippet_potential = aeo.featured_snippet_potential or aeo_snippet_potential
            aeo_questions_answered.extend(aeo.questions_answered or [])
            aeo_questions_to_add.extend(aeo.questions_to_add or [])
            aeo_paa.extend(aeo.paa_opportunities or [])

        if page_result.geo:
            geo = page_result.geo
            geo_originality = geo.originality_assessment or geo_originality
            geo_rationale = geo.strength_rationale or geo_rationale
            geo_citations.extend(geo.citation_worthy_elements or [])
            geo_risks.extend(geo.absorption_risks or [])
            geo_suggestions.extend(geo.defensibility_suggestions or [])

        if page_result.structure and page_result.structure.issues:
            structural_issues.extend(page_result.structure.issues)

    # Helper to build table rows
    def build_table_rows(items, max_items=5):
        rows = ""
        for item in items[:max_items]:
            rows += f"<tr><td>{item}</td></tr>"
        return rows

    # Helper to build action rows with impact
    def build_action_rows(recs, category_filter=None, max_items=5):
        filtered = recs
        if category_filter:
            filtered = [r for r in recs if r.category == category_filter]

        high = [r for r in filtered if r.priority.impact == "high"][:max_items]
        medium = [r for r in filtered if r.priority.impact == "medium"][:max_items]

        rows = ""
        for r in high:
            rows += f'<tr><td class="impact-high">High</td><td><strong>{r.title}</strong></td></tr>'
        for r in medium:
            rows += f'<tr><td class="impact-medium">Medium</td><td><strong>{r.title}</strong></td></tr>'
        return rows

    # Build executive summary priorities
    priorities_html = ""
    for i, rec in enumerate(top_priorities, 1):
        priorities_html += f'<div class="priority-item"><span class="priority-num">{i}</span><div><strong>{rec.title}</strong><p>{rec.description}</p></div></div>'

    # Build roadmap table
    roadmap_high = [r for r in all_recs if r.priority.impact == "high"][:6]
    roadmap_medium = [r for r in all_recs if r.priority.impact == "medium"][:6]

    roadmap_high_html = ""
    for r in roadmap_high:
        roadmap_high_html += f'<tr><td>{r.title}</td><td>{r.category}</td></tr>'

    roadmap_medium_html = ""
    for r in roadmap_medium:
        roadmap_medium_html += f'<tr><td>{r.title}</td><td>{r.category}</td></tr>'

    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>EngineOp Analysis Report</title>
    <style>
        @page {{
            size: A4;
            margin: 1.5cm 2cm;
            @top-right {{
                content: "EngineOp Report";
                font-size: 9pt;
                color: #6b7280;
            }}
            @bottom-center {{
                content: counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #6b7280;
            }}
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            font-size: 10pt;
            line-height: 1.5;
            color: #1f2937;
        }}

        .page-break {{
            page-break-after: always;
        }}

        /* Cover Page */
        .cover {{
            text-align: center;
            padding-top: 60pt;
        }}

        .cover .logo {{
            height: 56pt;
            margin-bottom: 24pt;
        }}

        .cover h1 {{
            font-size: 22pt;
            font-weight: 700;
            color: #111827;
            margin-bottom: 8pt;
        }}

        .cover .url {{
            display: inline-block;
            background: #f3f4f6;
            padding: 8pt 16pt;
            border-radius: 6pt;
            font-family: monospace;
            font-size: 11pt;
            color: #374151;
            margin: 16pt 0;
        }}

        .cover .date {{
            font-size: 11pt;
            color: #6b7280;
            margin-bottom: 40pt;
        }}

        .scores {{
            display: flex;
            justify-content: center;
            gap: 16pt;
            margin-top: 40pt;
        }}

        .score-card {{
            width: 140pt;
            padding: 20pt 16pt;
            border-radius: 8pt;
            text-align: center;
        }}

        .score-card.seo {{
            background: #e6f9f3;
            border: 2pt solid #0eb981;
        }}
        .score-card.aeo {{
            background: #eff6ff;
            border: 2pt solid #3b83f7;
        }}
        .score-card.geo {{
            background: #fef9e7;
            border: 2pt solid #f59e0d;
        }}

        .score-value {{
            font-size: 32pt;
            font-weight: 700;
            line-height: 1;
        }}
        .score-card.seo .score-value {{ color: #0eb981; }}
        .score-card.aeo .score-value {{ color: #3b83f7; }}
        .score-card.geo .score-value {{ color: #f59e0d; }}

        .score-label {{
            font-size: 12pt;
            font-weight: 600;
            margin-top: 8pt;
        }}
        .score-card.seo .score-label {{ color: #0eb981; }}
        .score-card.aeo .score-label {{ color: #3b83f7; }}
        .score-card.geo .score-label {{ color: #f59e0d; }}

        .score-rating {{
            font-size: 10pt;
            color: #6b7280;
            margin-top: 4pt;
        }}

        /* Executive Summary */
        .exec-summary {{
            padding-top: 20pt;
        }}

        .exec-summary h2 {{
            font-size: 18pt;
            font-weight: 700;
            color: #111827;
            border-bottom: 2pt solid #111827;
            padding-bottom: 8pt;
            margin-bottom: 20pt;
        }}

        .exec-summary h3 {{
            font-size: 12pt;
            font-weight: 600;
            color: #374151;
            margin: 20pt 0 12pt 0;
        }}

        .tldr {{
            background: #eff6ff;
            border-left: 4pt solid #3b83f7;
            padding: 12pt 16pt;
            margin-bottom: 20pt;
        }}

        .tldr p {{
            font-size: 11pt;
            color: #1e3a8a;
            line-height: 1.6;
        }}

        .priority-item {{
            display: flex;
            gap: 12pt;
            margin-bottom: 14pt;
            align-items: flex-start;
        }}

        .priority-num {{
            background: #111827;
            color: white;
            width: 22pt;
            height: 22pt;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11pt;
            font-weight: 600;
            flex-shrink: 0;
        }}

        .priority-item p {{
            font-size: 9pt;
            color: #6b7280;
            margin-top: 4pt;
        }}

        /* Section Pages */
        .section-page {{
            padding-top: 20pt;
        }}

        .section-header {{
            display: flex;
            align-items: center;
            gap: 10pt;
            margin-bottom: 20pt;
            padding-bottom: 10pt;
            border-bottom: 2pt solid #e5e7eb;
        }}

        .section-header h2 {{
            font-size: 18pt;
            font-weight: 700;
            color: #111827;
        }}

        .section-header .badge {{
            font-size: 9pt;
            font-weight: 600;
            padding: 4pt 10pt;
            border-radius: 12pt;
            color: white;
        }}

        .badge-seo {{ background: #0eb981; }}
        .badge-aeo {{ background: #3b83f7; }}
        .badge-geo {{ background: #f59e0d; }}

        .two-column {{
            display: flex;
            gap: 20pt;
        }}

        .column {{
            flex: 1;
        }}

        .subsection {{
            margin-bottom: 16pt;
        }}

        .subsection h3 {{
            font-size: 11pt;
            font-weight: 600;
            color: #374151;
            margin-bottom: 10pt;
            padding-bottom: 4pt;
            border-bottom: 1pt solid #e5e7eb;
        }}

        .subsection h4 {{
            font-size: 9pt;
            font-weight: 600;
            color: #6b7280;
            text-transform: uppercase;
            letter-spacing: 0.5pt;
            margin: 12pt 0 8pt 0;
        }}

        /* Tables */
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 9pt;
            margin-bottom: 12pt;
        }}

        th {{
            background: #f3f4f6;
            text-align: left;
            padding: 8pt 10pt;
            font-weight: 600;
            color: #374151;
            border-bottom: 1pt solid #e5e7eb;
        }}

        td {{
            padding: 8pt 10pt;
            border-bottom: 1pt solid #f3f4f6;
            color: #374151;
        }}

        .impact-high {{
            color: #dc2626;
            font-weight: 600;
            width: 60pt;
        }}

        .impact-medium {{
            color: #d97706;
            font-weight: 600;
            width: 60pt;
        }}

        /* Lists */
        ul {{
            margin: 0;
            padding-left: 16pt;
        }}

        li {{
            margin-bottom: 6pt;
            font-size: 9pt;
            color: #374151;
        }}

        .risk-list li {{
            color: #dc2626;
        }}

        /* Info Box */
        .info-box {{
            background: #f9fafb;
            border-radius: 6pt;
            padding: 12pt;
            margin-bottom: 12pt;
        }}

        .info-box p {{
            font-size: 10pt;
            color: #374151;
            line-height: 1.5;
        }}

        .info-box .label {{
            font-weight: 600;
            color: #111827;
        }}

        /* Roadmap */
        .roadmap h3 {{
            font-size: 12pt;
            font-weight: 600;
            margin: 20pt 0 12pt 0;
        }}

        .roadmap h3.high {{
            color: #dc2626;
        }}

        .roadmap h3.medium {{
            color: #d97706;
        }}

        .next-steps {{
            background: #f0fdf4;
            border: 1pt solid #bbf7d0;
            border-radius: 6pt;
            padding: 14pt;
            margin-top: 20pt;
        }}

        .next-steps h4 {{
            font-size: 11pt;
            font-weight: 600;
            color: #166534;
            margin-bottom: 10pt;
        }}

        .next-steps ol {{
            margin: 0;
            padding-left: 18pt;
        }}

        .next-steps li {{
            color: #166534;
            margin-bottom: 8pt;
        }}

        /* Footer */
        .footer {{
            margin-top: 30pt;
            padding-top: 12pt;
            border-top: 1pt solid #e5e7eb;
            text-align: center;
            font-size: 8pt;
            color: #9ca3af;
        }}
    </style>
</head>
<body>
    <!-- PAGE 1: Cover -->
    <div class="cover">
        <img src="{logo_data_uri}" class="logo" alt="EngineOp">
        <h1>SEO / AEO / GEO Analysis Report</h1>
        <div class="url">{result.url}</div>
        <div class="date">{result.timestamp.strftime('%B %d, %Y')}</div>

        <div class="scores">
            <div class="score-card seo">
                <div class="score-value">{seo_score}<span style="font-size: 14pt; color: #6b7280;">/10</span></div>
                <div class="score-label">SEO</div>
                <div class="score-rating">{_score_rating(seo_score)}</div>
            </div>
            <div class="score-card aeo">
                <div class="score-value">{aeo_score}<span style="font-size: 14pt; color: #6b7280;">/10</span></div>
                <div class="score-label">AEO</div>
                <div class="score-rating">{_score_rating(aeo_score)}</div>
            </div>
            <div class="score-card geo">
                <div class="score-value">{geo_score}<span style="font-size: 14pt; color: #6b7280;">/10</span></div>
                <div class="score-label">GEO</div>
                <div class="score-rating">{_score_rating(geo_score)}</div>
            </div>
        </div>
    </div>
    <div class="page-break"></div>

    <!-- PAGE 2: Executive Summary -->
    <div class="exec-summary">
        <h2>Executive Summary</h2>

        <div class="tldr">
            <p><strong>Bottom Line:</strong> {seo_rationale or "Analysis complete. See section details for findings."}</p>
        </div>

        <h3>Top 3 Priorities</h3>
        {priorities_html or "<p>No priority recommendations identified.</p>"}

        <h3>Why This Matters</h3>
        <p style="font-size: 10pt; line-height: 1.6; color: #374151;">
            {"Your site scores 'Good' across dimensions, but generic content is at risk of being absorbed by AI without citation. Competitors with more specific, original content will outrank you. The fix is not more content - it is more specific content." if (seo_score >= 6 and aeo_score >= 6 and geo_score >= 6) else "There are significant opportunities to improve discoverability and defensibility. Focus on the high-impact actions first."}
        </p>
    </div>
    <div class="page-break"></div>

    <!-- PAGE 3: SEO Analysis -->
    <div class="section-page">
        <div class="section-header">
            <h2>SEO Analysis</h2>
            <span class="badge badge-seo">Search Engine Optimization</span>
        </div>

        <div class="two-column">
            <div class="column">
                <div class="subsection">
                    <h3>What is Working</h3>
                    <div class="info-box">
                        <p><span class="label">Primary Topic:</span> {seo_primary_topic or "Not identified"}</p>
                    </div>
                    {f'<h4>Current Keywords</h4><ul>{"".join(f"<li>{kw}</li>" for kw in seo_current_keywords[:5])}</ul>' if seo_current_keywords else ""}
                </div>
            </div>
            <div class="column">
                <div class="subsection">
                    <h3>What is Missing</h3>
                    {f'<h4>Keyword Gaps</h4><ul>{"".join(f"<li>{kw}</li>" for kw in seo_missing_keywords[:5])}</ul>' if seo_missing_keywords else ""}
                    {f'<h4>Content Gaps</h4><ul>{"".join(f"<li>{gap}</li>" for gap in seo_content_gaps[:5])}</ul>' if seo_content_gaps else ""}
                </div>
            </div>
        </div>

        <div class="subsection">
            <h3>Actions</h3>
            <table>
                <tr><th>Impact</th><th>Action</th></tr>
                {build_action_rows(seo_recs) or "<tr><td colspan='2'>No SEO actions identified.</td></tr>"}
            </table>
        </div>
    </div>
    <div class="page-break"></div>

    <!-- PAGE 4: AEO Analysis -->
    <div class="section-page">
        <div class="section-header">
            <h2>AEO Analysis</h2>
            <span class="badge badge-aeo">Answer Engine Optimization</span>
        </div>

        <div class="subsection">
            <h3>Answer Readiness</h3>
            <div class="info-box">
                <p>{aeo_rationale or "No readiness assessment available."}</p>
                <p style="margin-top: 8pt;"><span class="label">Featured Snippet Potential:</span> {aeo_snippet_potential or "Not assessed"}</p>
            </div>
        </div>

        {f'''<div class="subsection">
            <h3>Structural Issues</h3>
            <table>
                <tr><th>Issue</th><th>Severity</th></tr>
                {"".join(f"<tr><td>{issue.issue}</td><td>{issue.severity.value}</td></tr>" for issue in structural_issues[:5])}
            </table>
        </div>''' if structural_issues else ""}

        <div class="two-column">
            <div class="column">
                <div class="subsection">
                    <h3>Questions You Answer</h3>
                    {f'<ul>{"".join(f"<li>{q}</li>" for q in aeo_questions_answered[:5])}</ul>' if aeo_questions_answered else "<p style='font-size: 9pt; color: #6b7280;'>None identified.</p>"}
                </div>
            </div>
            <div class="column">
                <div class="subsection">
                    <h3>Questions to Add</h3>
                    {f'<ul>{"".join(f"<li>{q}</li>" for q in aeo_questions_to_add[:5])}</ul>' if aeo_questions_to_add else "<p style='font-size: 9pt; color: #6b7280;'>None identified.</p>"}
                    {f'<h4>People Also Ask</h4><ul>{"".join(f"<li>{q}</li>" for q in aeo_paa[:3])}</ul>' if aeo_paa else ""}
                </div>
            </div>
        </div>

        <div class="subsection">
            <h3>Actions</h3>
            <table>
                <tr><th>Impact</th><th>Action</th></tr>
                {build_action_rows(aeo_recs) or "<tr><td colspan='2'>No AEO actions identified.</td></tr>"}
            </table>
        </div>
    </div>
    <div class="page-break"></div>

    <!-- PAGE 5: GEO Analysis -->
    <div class="section-page">
        <div class="section-header">
            <h2>GEO Analysis</h2>
            <span class="badge badge-geo">Generative Engine Optimization</span>
        </div>

        <div class="two-column">
            <div class="column">
                <div class="subsection">
                    <h3>AI Absorption Risks</h3>
                    <p style="font-size: 9pt; color: #6b7280; margin-bottom: 8pt;">Content AI may use without citing you:</p>
                    {f'<ul class="risk-list">{"".join(f"<li>{r}</li>" for r in geo_risks[:5])}</ul>' if geo_risks else "<p style='font-size: 9pt; color: #6b7280;'>None identified.</p>"}
                </div>

                <div class="subsection">
                    <h3>Defensibility Gaps</h3>
                    {f'<ul>{"".join(f"<li>{s}</li>" for s in geo_suggestions[:5])}</ul>' if geo_suggestions else "<p style='font-size: 9pt; color: #6b7280;'>None identified.</p>"}
                </div>
            </div>
            <div class="column">
                <div class="subsection">
                    <h3>What Makes You Citable</h3>
                    <div class="info-box">
                        <p><span class="label">Originality:</span> {geo_originality or "Not assessed"}</p>
                    </div>
                    {f'<h4>Citation-Worthy Elements</h4><ul>{"".join(f"<li>{c}</li>" for c in geo_citations[:5])}</ul>' if geo_citations else ""}
                </div>
            </div>
        </div>

        <div class="subsection">
            <h3>Actions</h3>
            <table>
                <tr><th>Impact</th><th>Action</th></tr>
                {build_action_rows(geo_recs) or "<tr><td colspan='2'>No GEO actions identified.</td></tr>"}
            </table>
        </div>
    </div>
    <div class="page-break"></div>

    <!-- PAGE 6: Action Roadmap -->
    <div class="section-page roadmap">
        <div class="section-header">
            <h2>Action Roadmap</h2>
        </div>

        <h3 class="high">High Impact - Do First</h3>
        <table>
            <tr><th>Action</th><th>Category</th></tr>
            {roadmap_high_html or "<tr><td colspan='2'>No high-impact actions.</td></tr>"}
        </table>

        <h3 class="medium">Medium Impact - Do Next</h3>
        <table>
            <tr><th>Action</th><th>Category</th></tr>
            {roadmap_medium_html or "<tr><td colspan='2'>No medium-impact actions.</td></tr>"}
        </table>

        <div class="next-steps">
            <h4>Next Steps</h4>
            <ol>
                <li>Start with one high-impact action from the list above</li>
                <li>Add specific, original content that competitors cannot replicate</li>
                <li>Reformat existing content for better scannability (bullets, tables)</li>
            </ol>
        </div>

        <div class="footer">
            Generated by EngineOp
        </div>
    </div>
</body>
</html>"""
