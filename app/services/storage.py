"""Storage service for analysis history using SQLite."""

import json
import os
import sqlite3
from datetime import datetime
from typing import Optional

from app.models import (
    AEOAnalysis,
    AnalysisMode,
    AnalysisResult,
    ContentClassification,
    ContentType,
    GEOAnalysis,
    KeywordData,
    PageAnalysisResult,
    PageData,
    PriorityScore,
    Recommendation,
    SEOAnalysis,
    Severity,
    StructuralIssue,
    StructureAnalysis,
)

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "analyses.db")


def _get_connection() -> sqlite3.Connection:
    """Get database connection, creating database if needed."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    _ensure_tables(conn)
    return conn


def _ensure_tables(conn: sqlite3.Connection):
    """Create tables if they don't exist."""
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id TEXT PRIMARY KEY,
            url TEXT NOT NULL,
            mode TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            overall_seo_score INTEGER DEFAULT 0,
            overall_aeo_score INTEGER DEFAULT 0,
            overall_geo_score INTEGER DEFAULT 0,
            data TEXT NOT NULL
        )
    """)
    conn.commit()


def _serialize_result(result: AnalysisResult) -> str:
    """Serialize AnalysisResult to JSON string."""
    from dataclasses import fields, is_dataclass
    from enum import Enum

    def serialize_obj(obj):
        # Check primitives and None first
        if obj is None or isinstance(obj, (str, int, float, bool)):
            return obj
        # Check enums before __dict__ check (enums have __dict__ too)
        elif isinstance(obj, Enum):
            return obj.value
        elif isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, list):
            return [serialize_obj(item) for item in obj]
        elif isinstance(obj, dict):
            return {k: serialize_obj(v) for k, v in obj.items()}
        elif is_dataclass(obj):
            d = {}
            for field in fields(obj):
                d[field.name] = serialize_obj(getattr(obj, field.name))
            return d
        else:
            return str(obj)

    return json.dumps(serialize_obj(result))


def _deserialize_result(data: str, row: sqlite3.Row) -> AnalysisResult:
    """Deserialize JSON string to AnalysisResult."""
    parsed = json.loads(data)

    # Reconstruct page results
    pages = []
    for page_data in parsed.get("pages", []):
        # Reconstruct PageData
        pd = page_data.get("page_data", {})
        page = PageData(
            url=pd.get("url", ""),
            title=pd.get("title", ""),
            meta_description=pd.get("meta_description"),
            headings=pd.get("headings", {}),
            paragraphs=pd.get("paragraphs", []),
            links=pd.get("links", []),
            word_count=pd.get("word_count", 0),
            has_faq_section=pd.get("has_faq_section", False),
            has_tldr_section=pd.get("has_tldr_section", False),
            has_schema_markup=pd.get("has_schema_markup", False),
            error=pd.get("error"),
        )

        # Reconstruct StructureAnalysis
        struct_data = page_data.get("structure", {})
        issues = []
        for issue_data in struct_data.get("issues", []):
            issues.append(StructuralIssue(
                issue=issue_data.get("issue", ""),
                severity=Severity(issue_data.get("severity", "medium")),
                recommendation=issue_data.get("recommendation", ""),
            ))
        structure = StructureAnalysis(
            issues=issues,
            has_h1=struct_data.get("has_h1", False),
            h1_count=struct_data.get("h1_count", 0),
            has_meta_description=struct_data.get("has_meta_description", False),
            meta_description_length=struct_data.get("meta_description_length", 0),
            word_count=struct_data.get("word_count", 0),
            heading_structure_valid=struct_data.get("heading_structure_valid", True),
        )

        # Reconstruct SEO
        seo = None
        seo_data = page_data.get("seo")
        if seo_data:
            seo = SEOAnalysis(
                primary_topic=seo_data.get("primary_topic", ""),
                target_keywords=seo_data.get("target_keywords", []),
                missing_keywords=seo_data.get("missing_keywords", []),
                content_gaps=seo_data.get("content_gaps", []),
                cluster_opportunities=seo_data.get("cluster_opportunities", []),
                quality_score=seo_data.get("quality_score", 0),
                quality_rationale=seo_data.get("quality_rationale", ""),
                recommendations=seo_data.get("recommendations", []),
            )

        # Reconstruct AEO
        aeo = None
        aeo_data = page_data.get("aeo")
        if aeo_data:
            aeo = AEOAnalysis(
                questions_answered=aeo_data.get("questions_answered", []),
                questions_to_add=aeo_data.get("questions_to_add", []),
                paa_opportunities=aeo_data.get("paa_opportunities", []),
                featured_snippet_potential=aeo_data.get("featured_snippet_potential", ""),
                format_quality=aeo_data.get("format_quality", ""),
                readiness_score=aeo_data.get("readiness_score", 0),
                readiness_rationale=aeo_data.get("readiness_rationale", ""),
                recommendations=aeo_data.get("recommendations", []),
            )

        # Reconstruct GEO
        geo = None
        geo_data = page_data.get("geo")
        if geo_data:
            geo = GEOAnalysis(
                originality_assessment=geo_data.get("originality_assessment", ""),
                citation_worthy_elements=geo_data.get("citation_worthy_elements", []),
                absorption_risks=geo_data.get("absorption_risks", []),
                defensibility_suggestions=geo_data.get("defensibility_suggestions", []),
                strength_score=geo_data.get("strength_score", 0),
                strength_rationale=geo_data.get("strength_rationale", ""),
                recommendations=geo_data.get("recommendations", []),
            )

        # Reconstruct Classification
        classification = None
        class_data = page_data.get("classification")
        if class_data:
            classification = ContentClassification(
                primary_type=ContentType(class_data.get("primary_type", "seo")),
                confidence=class_data.get("confidence", 0),
                explanation=class_data.get("explanation", ""),
                overlapping_types=[
                    ContentType(t) for t in class_data.get("overlapping_types", [])
                ],
            )

        pages.append(PageAnalysisResult(
            page_data=page,
            structure=structure,
            seo=seo,
            aeo=aeo,
            geo=geo,
            classification=classification,
        ))

    # Reconstruct recommendations
    recommendations = []
    for rec_data in parsed.get("recommendations", []):
        priority_data = rec_data.get("priority", {})
        priority = PriorityScore(
            score=priority_data.get("score", 0),
            impact=priority_data.get("impact", "medium"),
            effort=priority_data.get("effort", "medium"),
            keyword_volume=priority_data.get("keyword_volume"),
            factors=priority_data.get("factors", {}),
        )
        recommendations.append(Recommendation(
            title=rec_data.get("title", ""),
            description=rec_data.get("description", ""),
            category=rec_data.get("category", ""),
            priority=priority,
            rationale=rec_data.get("rationale", ""),
            action_items=rec_data.get("action_items", []),
        ))

    # Reconstruct keywords
    keywords = []
    for kw_data in parsed.get("keywords_used", []):
        keywords.append(KeywordData(
            keyword=kw_data.get("keyword", ""),
            volume=kw_data.get("volume"),
            difficulty=kw_data.get("difficulty"),
            cpc=kw_data.get("cpc"),
        ))

    return AnalysisResult(
        id=row["id"],
        url=row["url"],
        mode=AnalysisMode(row["mode"]),
        timestamp=datetime.fromisoformat(row["timestamp"]),
        pages=pages,
        recommendations=recommendations,
        overall_seo_score=row["overall_seo_score"],
        overall_aeo_score=row["overall_aeo_score"],
        overall_geo_score=row["overall_geo_score"],
        keywords_used=keywords,
        error=parsed.get("error"),
    )


def save_analysis(result: AnalysisResult) -> None:
    """Save analysis result to database."""
    conn = _get_connection()
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO analyses
            (id, url, mode, timestamp, overall_seo_score, overall_aeo_score, overall_geo_score, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.id,
                result.url,
                result.mode.value,
                result.timestamp.isoformat(),
                result.overall_seo_score,
                result.overall_aeo_score,
                result.overall_geo_score,
                _serialize_result(result),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def get_analysis(analysis_id: str) -> Optional[AnalysisResult]:
    """Get analysis by ID."""
    conn = _get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
        ).fetchone()

        if not row:
            return None

        return _deserialize_result(row["data"], row)
    finally:
        conn.close()


def get_all_analyses() -> list[AnalysisResult]:
    """Get all analyses, sorted by timestamp descending."""
    conn = _get_connection()
    try:
        rows = conn.execute(
            "SELECT * FROM analyses ORDER BY timestamp DESC"
        ).fetchall()

        results = []
        for row in rows:
            try:
                result = _deserialize_result(row["data"], row)
                results.append(result)
            except Exception:
                # Skip corrupted entries
                continue

        return results
    finally:
        conn.close()


def delete_analysis(analysis_id: str) -> bool:
    """Delete analysis by ID."""
    conn = _get_connection()
    try:
        cursor = conn.execute("DELETE FROM analyses WHERE id = ?", (analysis_id,))
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()
