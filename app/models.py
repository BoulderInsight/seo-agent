"""Data models for the SEO analysis tool."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class AnalysisMode(Enum):
    """Analysis mode enum."""

    SINGLE_PAGE = "single"
    FULL_SITE = "full"


class Severity(Enum):
    """Severity level for issues."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ContentType(Enum):
    """Content classification type."""

    SEO = "seo"
    AEO = "aeo"
    GEO = "geo"
    SEO_AEO = "seo_aeo"
    SEO_GEO = "seo_geo"
    AEO_GEO = "aeo_geo"
    ALL = "all"


@dataclass
class KeywordData:
    """Keyword data from CSV import."""

    keyword: str
    volume: Optional[int] = None
    difficulty: Optional[float] = None
    cpc: Optional[float] = None


@dataclass
class PageData:
    """Extracted data from a crawled page."""

    url: str
    title: str
    meta_description: Optional[str]
    headings: dict[str, list[str]]  # h1, h2, etc.
    paragraphs: list[str]
    links: list[str]
    word_count: int
    has_faq_section: bool = False
    has_tldr_section: bool = False
    has_schema_markup: bool = False
    error: Optional[str] = None


@dataclass
class StructuralIssue:
    """A structural issue found in page analysis."""

    issue: str
    severity: Severity
    recommendation: str


@dataclass
class StructureAnalysis:
    """Results of structural analysis."""

    issues: list[StructuralIssue] = field(default_factory=list)
    has_h1: bool = False
    h1_count: int = 0
    has_meta_description: bool = False
    meta_description_length: int = 0
    word_count: int = 0
    heading_structure_valid: bool = True


@dataclass
class SEOAnalysis:
    """SEO analysis results."""

    primary_topic: str
    target_keywords: list[str]
    missing_keywords: list[str]
    content_gaps: list[str]
    cluster_opportunities: list[str]
    quality_score: int  # 1-10
    quality_rationale: str
    recommendations: list[str]


@dataclass
class AEOAnalysis:
    """AEO analysis results."""

    questions_answered: list[str]
    questions_to_add: list[str]
    paa_opportunities: list[str]  # People Also Ask
    featured_snippet_potential: str
    format_quality: str
    readiness_score: int  # 1-10
    readiness_rationale: str
    recommendations: list[str]


@dataclass
class GEOAnalysis:
    """GEO analysis results."""

    originality_assessment: str
    citation_worthy_elements: list[str]
    absorption_risks: list[str]
    defensibility_suggestions: list[str]
    strength_score: int  # 1-10
    strength_rationale: str
    recommendations: list[str]


@dataclass
class ContentClassification:
    """Content classification result."""

    primary_type: ContentType
    confidence: float  # 0-1
    explanation: str
    overlapping_types: list[ContentType] = field(default_factory=list)


@dataclass
class PriorityScore:
    """Priority score for a recommendation."""

    score: int  # 1-100
    impact: str  # high/medium/low
    effort: str  # high/medium/low
    keyword_volume: Optional[int] = None
    factors: dict[str, int] = field(default_factory=dict)


@dataclass
class Recommendation:
    """A single recommendation."""

    title: str
    description: str
    category: str  # SEO, AEO, GEO, Structure
    priority: PriorityScore
    rationale: str
    action_items: list[str] = field(default_factory=list)


@dataclass
class PageAnalysisResult:
    """Complete analysis result for a single page."""

    page_data: PageData
    structure: StructureAnalysis
    seo: Optional[SEOAnalysis] = None
    aeo: Optional[AEOAnalysis] = None
    geo: Optional[GEOAnalysis] = None
    classification: Optional[ContentClassification] = None


@dataclass
class AnalysisResult:
    """Complete analysis result."""

    id: str
    url: str
    mode: AnalysisMode
    timestamp: datetime
    pages: list[PageAnalysisResult]
    recommendations: list[Recommendation]
    overall_seo_score: int = 0
    overall_aeo_score: int = 0
    overall_geo_score: int = 0
    keywords_used: list[KeywordData] = field(default_factory=list)
    error: Optional[str] = None
