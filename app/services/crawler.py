"""Web crawler service for fetching and extracting page content."""

import re
import time
from typing import Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from app.models import PageData

# Default headers for requests
DEFAULT_HEADERS = {
    "User-Agent": "SEOAgent/1.0 (Web Analysis Tool; +https://github.com/seo-agent)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# Request timeout in seconds
TIMEOUT = 10

# Delay between requests in seconds
CRAWL_DELAY = 1


def crawl_page(url: str) -> PageData:
    """
    Fetch and extract content from a single URL.

    Args:
        url: The URL to crawl

    Returns:
        PageData object with extracted content
    """
    try:
        response = requests.get(url, headers=DEFAULT_HEADERS, timeout=TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "lxml")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Extract meta description
        meta_desc = None
        meta_tag = soup.find("meta", attrs={"name": re.compile(r"description", re.I)})
        if meta_tag and meta_tag.get("content"):
            meta_desc = meta_tag["content"]

        # Extract headings
        headings: dict[str, list[str]] = {}
        for level in range(1, 7):
            tag_name = f"h{level}"
            found = soup.find_all(tag_name)
            if found:
                headings[tag_name] = [h.get_text(strip=True) for h in found]

        # Extract paragraphs
        paragraphs = []
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Skip very short paragraphs
                paragraphs.append(text)

        # Calculate word count
        body_text = soup.get_text(separator=" ", strip=True)
        word_count = len(body_text.split())

        # Extract internal links
        links = []
        base_domain = urlparse(url).netloc
        for a in soup.find_all("a", href=True):
            href = a["href"]
            full_url = urljoin(url, href)
            parsed = urlparse(full_url)
            if parsed.netloc == base_domain and parsed.scheme in ("http", "https"):
                # Normalize URL (remove fragments)
                normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                if parsed.query:
                    normalized += f"?{parsed.query}"
                if normalized not in links:
                    links.append(normalized)

        # Check for FAQ section
        has_faq = bool(
            soup.find(id=re.compile(r"faq", re.I))
            or soup.find(class_=re.compile(r"faq", re.I))
            or soup.find(string=re.compile(r"frequently\s+asked\s+questions", re.I))
        )

        # Check for TLDR/Summary section
        has_tldr = bool(
            soup.find(id=re.compile(r"(tldr|summary|key-?takeaway)", re.I))
            or soup.find(class_=re.compile(r"(tldr|summary|key-?takeaway)", re.I))
        )

        # Check for schema.org markup
        has_schema = bool(
            soup.find("script", type="application/ld+json")
            or soup.find(attrs={"itemtype": re.compile(r"schema\.org", re.I)})
        )

        return PageData(
            url=url,
            title=title,
            meta_description=meta_desc,
            headings=headings,
            paragraphs=paragraphs,
            links=links,
            word_count=word_count,
            has_faq_section=has_faq,
            has_tldr_section=has_tldr,
            has_schema_markup=has_schema,
        )

    except requests.Timeout:
        return PageData(
            url=url,
            title="",
            meta_description=None,
            headings={},
            paragraphs=[],
            links=[],
            word_count=0,
            error="Request timed out after 10 seconds",
        )
    except requests.RequestException as e:
        return PageData(
            url=url,
            title="",
            meta_description=None,
            headings={},
            paragraphs=[],
            links=[],
            word_count=0,
            error=f"Failed to fetch page: {str(e)}",
        )


def crawl_site(
    start_url: str,
    max_pages: int = 10,
    progress_callback: Optional[callable] = None,
) -> list[PageData]:
    """
    Crawl multiple pages from a site starting from the given URL.

    Args:
        start_url: The starting URL for the crawl
        max_pages: Maximum number of pages to crawl (1-50)
        progress_callback: Optional callback for progress updates

    Returns:
        List of PageData objects for each crawled page
    """
    max_pages = min(max(max_pages, 1), 50)

    crawled_urls: set[str] = set()
    to_crawl: list[str] = [start_url]
    results: list[PageData] = []

    base_domain = urlparse(start_url).netloc

    while to_crawl and len(results) < max_pages:
        url = to_crawl.pop(0)

        # Normalize URL
        parsed = urlparse(url)
        normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized_url += f"?{parsed.query}"

        # Skip if already crawled
        if normalized_url in crawled_urls:
            continue

        # Skip if different domain
        if parsed.netloc != base_domain:
            continue

        crawled_urls.add(normalized_url)

        if progress_callback:
            progress_callback(
                f"Crawling page {len(results) + 1}/{max_pages}...",
                int((len(results) / max_pages) * 30),
            )

        # Crawl the page
        page_data = crawl_page(normalized_url)
        results.append(page_data)

        # Add discovered links to crawl queue
        if not page_data.error:
            for link in page_data.links:
                if link not in crawled_urls and link not in to_crawl:
                    to_crawl.append(link)

        # Polite delay between requests
        if to_crawl and len(results) < max_pages:
            time.sleep(CRAWL_DELAY)

    return results
