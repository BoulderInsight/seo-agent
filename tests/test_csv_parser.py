"""Tests for CSV parser service."""

import io

import pytest

from app.services.csv_parser import parse_keyword_csv


class TestCSVParser:
    """Test cases for CSV parser."""

    def test_parse_semrush_format(self):
        """Test parsing SEMrush CSV format."""
        csv_content = """Keyword,Search Volume,Keyword Difficulty,CPC
seo tools,12000,45,2.50
keyword research,8500,38,1.80
backlink checker,5000,52,3.20"""

        file = io.BytesIO(csv_content.encode("utf-8"))
        keywords = parse_keyword_csv(file)

        assert len(keywords) == 3
        assert keywords[0].keyword == "seo tools"
        assert keywords[0].volume == 12000
        assert keywords[0].difficulty == 45.0
        assert keywords[0].cpc == 2.50

    def test_parse_ahrefs_format(self):
        """Test parsing Ahrefs CSV format."""
        csv_content = """Keyword,Volume,KD,CPC
content marketing,15000,42,2.10
link building,9000,55,3.50
seo audit,6500,35,1.90"""

        file = io.BytesIO(csv_content.encode("utf-8"))
        keywords = parse_keyword_csv(file)

        assert len(keywords) == 3
        assert keywords[0].keyword == "content marketing"
        assert keywords[0].volume == 15000
        assert keywords[0].difficulty == 42.0

    def test_handles_missing_columns(self):
        """Test handling CSV with missing optional columns."""
        csv_content = """Keyword,Volume
test keyword,1000
another keyword,500"""

        file = io.BytesIO(csv_content.encode("utf-8"))
        keywords = parse_keyword_csv(file)

        assert len(keywords) == 2
        assert keywords[0].keyword == "test keyword"
        assert keywords[0].volume == 1000
        assert keywords[0].difficulty is None
        assert keywords[0].cpc is None

    def test_handles_empty_values(self):
        """Test handling empty or N/A values."""
        csv_content = """Keyword,Volume,KD,CPC
keyword one,1000,50,1.00
keyword two,-,N/A,
keyword three,500,,0.50"""

        file = io.BytesIO(csv_content.encode("utf-8"))
        keywords = parse_keyword_csv(file)

        assert len(keywords) == 3
        assert keywords[1].volume is None
        assert keywords[1].difficulty is None
        assert keywords[1].cpc is None
        assert keywords[2].difficulty is None

    def test_handles_formatted_numbers(self):
        """Test handling numbers with commas and currency symbols."""
        # Note: CSV values with commas must be quoted
        csv_content = """Keyword,Search Volume,CPC
high volume,"10,000","$5.99"
medium volume,"1,500","$2.50" """

        file = io.BytesIO(csv_content.encode("utf-8"))
        keywords = parse_keyword_csv(file)

        assert len(keywords) == 2
        assert keywords[0].volume == 10000
        assert keywords[0].cpc == 5.99

    def test_raises_error_for_missing_keyword_column(self):
        """Test error raised when Keyword column is missing."""
        csv_content = """Volume,Difficulty,CPC
1000,50,1.00
500,30,0.50"""

        file = io.BytesIO(csv_content.encode("utf-8"))

        with pytest.raises(ValueError) as exc_info:
            parse_keyword_csv(file)

        assert "Keyword" in str(exc_info.value)

    def test_raises_error_for_empty_file(self):
        """Test error raised for empty file."""
        csv_content = ""

        file = io.BytesIO(csv_content.encode("utf-8"))

        with pytest.raises(ValueError):
            parse_keyword_csv(file)

    def test_skips_empty_keyword_rows(self):
        """Test that rows with empty keywords are skipped."""
        csv_content = """Keyword,Volume
valid keyword,1000
,500
another valid,800"""

        file = io.BytesIO(csv_content.encode("utf-8"))
        keywords = parse_keyword_csv(file)

        assert len(keywords) == 2
        assert keywords[0].keyword == "valid keyword"
        assert keywords[1].keyword == "another valid"

    def test_handles_utf8_with_bom(self):
        """Test handling UTF-8 files with BOM."""
        csv_content = "\ufeffKeyword,Volume\ntest keyword,1000"

        file = io.BytesIO(csv_content.encode("utf-8-sig"))
        keywords = parse_keyword_csv(file)

        assert len(keywords) == 1
        assert keywords[0].keyword == "test keyword"
