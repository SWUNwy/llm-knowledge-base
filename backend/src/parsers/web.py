from __future__ import annotations
"""Web page parser using readability-lxml and BeautifulSoup."""

from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from readability import Document

from src.parsers.base import BaseParser, ParseResult


class WebParser(BaseParser):
    """Parser for web pages.

    Uses readability-lxml for content extraction and BeautifulSoup for HTML cleaning.
    Supports both URL and local file parsing.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        """Initialize the web parser.

        Args:
            timeout: HTTP request timeout in seconds.
        """
        self.timeout = timeout

    async def parse_url(self, url: str) -> ParseResult:
        """Parse content from a web URL.

        Args:
            url: The URL to fetch and parse.

        Returns:
            ParseResult with the extracted content.
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
                html = response.text

            return self._parse_html(html, source_url=url)
        except httpx.HTTPStatusError as e:
            return ParseResult(
                success=False,
                error=f"HTTP error {e.response.status_code}: {e.response.reason_phrase}",
            )
        except httpx.RequestError as e:
            return ParseResult(success=False, error=f"Request error: {str(e)}")
        except Exception as e:
            return ParseResult(success=False, error=f"Unexpected error: {str(e)}")

    async def parse_file(self, path: Path) -> ParseResult:
        """Parse content from a local HTML file.

        Args:
            path: Path to the local HTML file to parse.

        Returns:
            ParseResult with the extracted content.
        """
        if not path.exists():
            return ParseResult(
                success=False,
                error=f"File not found: {path}",
            )

        if not path.is_file():
            return ParseResult(
                success=False,
                error=f"Path is not a file: {path}",
            )

        try:
            html = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                html = path.read_text(encoding="latin-1")
            except Exception as e:
                return ParseResult(success=False, error=f"Failed to read file: {str(e)}")
        except Exception as e:
            return ParseResult(success=False, error=f"Failed to read file: {str(e)}")

        return self._parse_html(html, source_url=None)

    def _parse_html(self, html: str, source_url: str | None = None) -> ParseResult:
        """Parse HTML content and extract readable content.

        Args:
            html: The HTML content to parse.
            source_url: Optional source URL for resolving relative image URLs.

        Returns:
            ParseResult with the extracted content.
        """
        try:
            # Use readability for content extraction
            doc = Document(html)
            title = doc.title()
            summary_html = doc.summary()

            # Parse with BeautifulSoup for cleaning and metadata extraction
            soup = BeautifulSoup(html, "lxml")
            summary_soup = BeautifulSoup(summary_html, "lxml")

            # Extract metadata
            metadata: dict[str, Any] = {}
            self._extract_metadata(soup, metadata)

            if source_url:
                metadata["source_url"] = source_url

            # Extract clean text content
            content = self._extract_text(summary_soup)

            # Extract images
            images = self._extract_images(summary_soup, source_url)

            return ParseResult(
                success=True,
                title=title,
                content=content,
                metadata=metadata,
                images=images,
            )
        except Exception as e:
            return ParseResult(success=False, error=f"Failed to parse HTML: {str(e)}")

    def _extract_metadata(self, soup: BeautifulSoup, metadata: dict[str, Any]) -> None:
        """Extract metadata from HTML head.

        Args:
            soup: BeautifulSoup instance of the HTML.
            metadata: Dictionary to store extracted metadata.
        """
        # Extract author from meta tag
        author_meta = soup.find("meta", attrs={"name": "author"})
        if author_meta and author_meta.get("content"):
            metadata["author"] = author_meta["content"]

        # Extract description
        desc_meta = soup.find("meta", attrs={"name": "description"})
        if desc_meta and desc_meta.get("content"):
            metadata["description"] = desc_meta["content"]

        # Extract keywords
        keywords_meta = soup.find("meta", attrs={"name": "keywords"})
        if keywords_meta and keywords_meta.get("content"):
            metadata["keywords"] = keywords_meta["content"]

        # Extract Open Graph metadata
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            metadata["og_title"] = og_title["content"]

        og_desc = soup.find("meta", property="og:description")
        if og_desc and og_desc.get("content"):
            metadata["og_description"] = og_desc["content"]

    def _extract_text(self, soup: BeautifulSoup) -> str:
        """Extract clean text from HTML.

        Args:
            soup: BeautifulSoup instance of the HTML.

        Returns:
            Clean text content with normalized whitespace.
        """
        # Remove script and style elements
        for element in soup.find_all(["script", "style", "nav", "footer", "header"]):
            element.decompose()

        # Get text and normalize whitespace
        text = soup.get_text(separator="\n", strip=True)

        # Remove excessive newlines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return "\n\n".join(lines)

    def _extract_images(self, soup: BeautifulSoup, source_url: str | None) -> list[str]:
        """Extract image URLs from HTML.

        Args:
            soup: BeautifulSoup instance of the HTML.
            source_url: Source URL for resolving relative URLs.

        Returns:
            List of absolute image URLs.
        """
        images: list[str] = []

        for img in soup.find_all("img"):
            src = img.get("src")
            if not src or not isinstance(src, str):
                continue

            # Skip data URLs and empty sources
            if src.startswith("data:") or not src.strip():
                continue

            # Resolve relative URLs if source_url is available
            if source_url:
                absolute_url: str = urljoin(source_url, src)
            else:
                # For local files, only include absolute URLs
                if src.startswith(("http://", "https://")):
                    absolute_url = src
                else:
                    continue

            # Only include http/https URLs
            parsed = urlparse(absolute_url)
            if parsed.scheme in ("http", "https"):
                images.append(absolute_url)

        return images
