"""Tests for structure analyzer service."""

from app.models import PageData, Severity
from app.services.structure_analyzer import analyze_structure


class TestStructureAnalyzer:
    """Test cases for structure analyzer."""

    def create_page_data(self, **kwargs):
        """Helper to create PageData with defaults."""
        defaults = {
            "url": "https://example.com",
            "title": "Test Page Title",
            "meta_description": "This is a test meta description that is a good length.",
            "headings": {"h1": ["Main Heading"]},
            "paragraphs": ["Test paragraph."] * 20,
            "links": [],
            "word_count": 500,
            "has_faq_section": False,
            "has_tldr_section": False,
            "has_schema_markup": False,
        }
        defaults.update(kwargs)
        return PageData(**defaults)

    def test_detects_missing_h1(self):
        """Test detection of missing H1 heading."""
        page = self.create_page_data(headings={})
        result = analyze_structure(page)

        assert not result.has_h1
        assert result.h1_count == 0

        h1_issues = [i for i in result.issues if "H1" in i.issue]
        assert len(h1_issues) == 1
        assert h1_issues[0].severity == Severity.HIGH

    def test_detects_multiple_h1(self):
        """Test detection of multiple H1 headings."""
        page = self.create_page_data(headings={"h1": ["First H1", "Second H1"]})
        result = analyze_structure(page)

        assert result.has_h1
        assert result.h1_count == 2

        h1_issues = [i for i in result.issues if "Multiple H1" in i.issue]
        assert len(h1_issues) == 1
        assert h1_issues[0].severity == Severity.MEDIUM

    def test_detects_missing_meta_description(self):
        """Test detection of missing meta description."""
        page = self.create_page_data(meta_description=None)
        result = analyze_structure(page)

        assert not result.has_meta_description

        meta_issues = [i for i in result.issues if "meta description" in i.issue.lower()]
        assert len(meta_issues) >= 1

    def test_detects_short_meta_description(self):
        """Test detection of too-short meta description."""
        page = self.create_page_data(meta_description="Too short")
        result = analyze_structure(page)

        meta_issues = [i for i in result.issues if "meta description too short" in i.issue.lower()]
        assert len(meta_issues) == 1
        assert meta_issues[0].severity == Severity.MEDIUM

    def test_detects_long_meta_description(self):
        """Test detection of too-long meta description."""
        long_meta = "A" * 200
        page = self.create_page_data(meta_description=long_meta)
        result = analyze_structure(page)

        meta_issues = [i for i in result.issues if "too long" in i.issue.lower()]
        assert len(meta_issues) == 1
        assert meta_issues[0].severity == Severity.LOW

    def test_detects_thin_content(self):
        """Test detection of thin content."""
        page = self.create_page_data(word_count=100)
        result = analyze_structure(page)

        assert result.word_count == 100

        thin_issues = [i for i in result.issues if "thin" in i.issue.lower()]
        assert len(thin_issues) == 1
        assert thin_issues[0].severity == Severity.HIGH

    def test_detects_very_long_content(self):
        """Test detection of very long content."""
        page = self.create_page_data(word_count=4000)
        result = analyze_structure(page)

        long_issues = [i for i in result.issues if "very long" in i.issue.lower()]
        assert len(long_issues) == 1
        assert long_issues[0].severity == Severity.LOW

    def test_detects_skipped_heading_levels(self):
        """Test detection of skipped heading levels."""
        page = self.create_page_data(headings={"h1": ["Main"], "h3": ["Subheading"]})
        result = analyze_structure(page)

        assert not result.heading_structure_valid

        skip_issues = [i for i in result.issues if "Skipped heading" in i.issue]
        assert len(skip_issues) >= 1

    def test_detects_missing_faq_section(self):
        """Test detection of missing FAQ section."""
        page = self.create_page_data(has_faq_section=False)
        result = analyze_structure(page)

        faq_issues = [i for i in result.issues if "FAQ" in i.issue]
        assert len(faq_issues) == 1
        assert faq_issues[0].severity == Severity.LOW

    def test_detects_missing_schema_markup(self):
        """Test detection of missing schema markup."""
        page = self.create_page_data(has_schema_markup=False)
        result = analyze_structure(page)

        schema_issues = [i for i in result.issues if "schema" in i.issue.lower()]
        assert len(schema_issues) == 1
        assert schema_issues[0].severity == Severity.MEDIUM

    def test_detects_missing_title(self):
        """Test detection of missing title."""
        page = self.create_page_data(title="")
        result = analyze_structure(page)

        title_issues = [i for i in result.issues if "title" in i.issue.lower()]
        assert len(title_issues) >= 1
        assert any(i.severity == Severity.CRITICAL for i in title_issues)

    def test_well_structured_page_has_few_issues(self):
        """Test that a well-structured page has minimal issues."""
        page = self.create_page_data(
            title="A Good Page Title That Is Long Enough",
            meta_description="A meta description that is the right length for SEO purposes and provides good context about the page content.",
            headings={"h1": ["Main Heading"], "h2": ["Section One", "Section Two"]},
            word_count=800,
            has_faq_section=True,
            has_schema_markup=True,
        )
        result = analyze_structure(page)

        # Should only have low-severity issues (like missing TLDR for long content)
        high_issues = [i for i in result.issues if i.severity in (Severity.HIGH, Severity.CRITICAL)]
        assert len(high_issues) == 0
