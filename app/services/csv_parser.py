"""CSV parser for keyword data from SEMrush and Ahrefs."""

import csv
import io
from typing import BinaryIO

from app.models import KeywordData

# Column name mappings for different formats
COLUMN_MAPPINGS = {
    "keyword": ["keyword", "keywords", "search term", "query"],
    "volume": ["search volume", "volume", "avg. monthly searches", "monthly searches"],
    "difficulty": ["keyword difficulty", "kd", "difficulty", "kd %", "seo difficulty"],
    "cpc": ["cpc", "cpc (usd)", "cpc ($)", "cost per click"],
}


def normalize_column_name(name: str) -> str | None:
    """Normalize a column name to our standard format."""
    name_lower = name.lower().strip()
    for standard_name, variations in COLUMN_MAPPINGS.items():
        if name_lower in variations:
            return standard_name
    return None


def parse_value(value: str, value_type: str) -> int | float | None:
    """Parse a string value to the appropriate type."""
    if not value or value.strip() in ("", "-", "n/a", "N/A"):
        return None

    value = value.strip().replace(",", "").replace("$", "").replace("%", "")

    try:
        if value_type == "volume":
            return int(float(value))
        else:
            return float(value)
    except (ValueError, TypeError):
        return None


def parse_keyword_csv(file: BinaryIO) -> list[KeywordData]:
    """
    Parse a keyword CSV file from SEMrush or Ahrefs format.

    Args:
        file: File object containing CSV data

    Returns:
        List of KeywordData objects

    Raises:
        ValueError: If the file cannot be parsed
    """
    try:
        # Read file content
        content = file.read()
        if isinstance(content, bytes):
            # Try different encodings
            for encoding in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
                try:
                    text = content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Unable to decode file. Please ensure it's a valid CSV file.")
        else:
            text = content

        # Parse CSV
        reader = csv.DictReader(io.StringIO(text))

        if not reader.fieldnames:
            raise ValueError("CSV file appears to be empty or has no headers")

        # Map columns (strip BOM and whitespace from field names)
        column_map: dict[str, str] = {}
        for field in reader.fieldnames:
            # Strip BOM and whitespace
            clean_field = field.strip().lstrip("\ufeff").lstrip("\ufeff")
            normalized = normalize_column_name(clean_field)
            if normalized:
                column_map[normalized] = field

        if "keyword" not in column_map:
            raise ValueError(
                "CSV must contain a 'Keyword' column. "
                f"Found columns: {', '.join(reader.fieldnames)}"
            )

        # Parse rows
        keywords: list[KeywordData] = []
        for row_num, row in enumerate(reader, start=2):
            keyword_value = row.get(column_map["keyword"], "").strip()
            if not keyword_value:
                continue

            keyword_data = KeywordData(
                keyword=keyword_value,
                volume=parse_value(
                    row.get(column_map.get("volume", ""), ""), "volume"
                ),
                difficulty=parse_value(
                    row.get(column_map.get("difficulty", ""), ""), "difficulty"
                ),
                cpc=parse_value(
                    row.get(column_map.get("cpc", ""), ""), "cpc"
                ),
            )
            keywords.append(keyword_data)

        if not keywords:
            raise ValueError("No valid keyword data found in CSV")

        return keywords

    except csv.Error as e:
        raise ValueError(f"CSV parsing error: {e}")
    except Exception as e:
        if isinstance(e, ValueError):
            raise
        raise ValueError(f"Failed to parse CSV: {e}")
