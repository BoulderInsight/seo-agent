"""Content structure analyzer service."""

from app.models import PageData, Severity, StructuralIssue, StructureAnalysis


def analyze_structure(page_data: PageData) -> StructureAnalysis:
    """
    Analyze page structure and identify structural issues.

    Args:
        page_data: The extracted page data to analyze

    Returns:
        StructureAnalysis object with findings
    """
    issues: list[StructuralIssue] = []

    # Check H1 presence
    h1_list = page_data.headings.get("h1", [])
    h1_count = len(h1_list)
    has_h1 = h1_count > 0

    if h1_count == 0:
        issues.append(
            StructuralIssue(
                issue="Missing H1 heading",
                severity=Severity.HIGH,
                recommendation="Add a clear, descriptive H1 heading that includes your primary keyword",
            )
        )
    elif h1_count > 1:
        issues.append(
            StructuralIssue(
                issue=f"Multiple H1 headings found ({h1_count})",
                severity=Severity.MEDIUM,
                recommendation="Use only one H1 heading per page. Convert secondary H1s to H2s",
            )
        )

    # Check meta description
    meta_desc = page_data.meta_description
    has_meta = meta_desc is not None and len(meta_desc.strip()) > 0
    meta_length = len(meta_desc) if meta_desc else 0

    if not has_meta:
        issues.append(
            StructuralIssue(
                issue="Missing meta description",
                severity=Severity.HIGH,
                recommendation="Add a compelling meta description (150-160 characters) that summarizes the page content",
            )
        )
    elif meta_length < 70:
        issues.append(
            StructuralIssue(
                issue=f"Meta description too short ({meta_length} characters)",
                severity=Severity.MEDIUM,
                recommendation="Expand meta description to 150-160 characters for optimal display in search results",
            )
        )
    elif meta_length > 160:
        issues.append(
            StructuralIssue(
                issue=f"Meta description too long ({meta_length} characters)",
                severity=Severity.LOW,
                recommendation="Trim meta description to under 160 characters to avoid truncation in search results",
            )
        )

    # Check heading hierarchy
    heading_structure_valid = True
    prev_level = 0
    for level in range(1, 7):
        tag = f"h{level}"
        if tag in page_data.headings and page_data.headings[tag]:
            if level > prev_level + 1 and prev_level > 0:
                heading_structure_valid = False
                issues.append(
                    StructuralIssue(
                        issue=f"Skipped heading level: H{prev_level} to H{level}",
                        severity=Severity.LOW,
                        recommendation=f"Use H{prev_level + 1} before H{level} to maintain proper document structure",
                    )
                )
            prev_level = level

    # Check content length
    word_count = page_data.word_count

    if word_count < 300:
        issues.append(
            StructuralIssue(
                issue=f"Thin content ({word_count} words)",
                severity=Severity.HIGH,
                recommendation="Expand content to at least 300 words. Consider adding more detailed information, examples, or FAQs",
            )
        )
    elif word_count > 3000:
        issues.append(
            StructuralIssue(
                issue=f"Very long content ({word_count} words)",
                severity=Severity.LOW,
                recommendation="Consider breaking into multiple pages or adding a table of contents and summary section",
            )
        )

    # Check for FAQ section
    if not page_data.has_faq_section:
        issues.append(
            StructuralIssue(
                issue="No FAQ section detected",
                severity=Severity.LOW,
                recommendation="Consider adding an FAQ section to answer common questions and improve AEO",
            )
        )

    # Check for TLDR/Summary
    if word_count > 1000 and not page_data.has_tldr_section:
        issues.append(
            StructuralIssue(
                issue="Long content without summary section",
                severity=Severity.LOW,
                recommendation="Add a TL;DR or key takeaways section at the top for long-form content",
            )
        )

    # Check for schema markup
    if not page_data.has_schema_markup:
        issues.append(
            StructuralIssue(
                issue="No schema.org markup detected",
                severity=Severity.MEDIUM,
                recommendation="Add structured data (JSON-LD) to help search engines understand your content",
            )
        )

    # Check title
    if not page_data.title:
        issues.append(
            StructuralIssue(
                issue="Missing page title",
                severity=Severity.CRITICAL,
                recommendation="Add a descriptive title tag that includes your primary keyword",
            )
        )
    elif len(page_data.title) < 30:
        issues.append(
            StructuralIssue(
                issue=f"Title tag too short ({len(page_data.title)} characters)",
                severity=Severity.MEDIUM,
                recommendation="Expand title to 50-60 characters for better CTR in search results",
            )
        )
    elif len(page_data.title) > 60:
        issues.append(
            StructuralIssue(
                issue=f"Title tag too long ({len(page_data.title)} characters)",
                severity=Severity.LOW,
                recommendation="Shorten title to under 60 characters to avoid truncation in search results",
            )
        )

    return StructureAnalysis(
        issues=issues,
        has_h1=has_h1,
        h1_count=h1_count,
        has_meta_description=has_meta,
        meta_description_length=meta_length,
        word_count=word_count,
        heading_structure_valid=heading_structure_valid,
    )
