"""Tests for the web parser module."""

from pathlib import Path

import pytest

from src.parsers.base import ParseResult
from src.parsers.web import WebParser


class TestWebParser:
    """Tests for WebParser class."""

    @pytest.fixture
    def parser(self) -> WebParser:
        """Create a WebParser instance."""
        return WebParser()

    @pytest.fixture
    def simple_html_path(self) -> Path:
        """Get path to the simple.html test fixture."""
        return Path(__file__).parent.parent / "fixtures" / "html" / "simple.html"

    async def test_parse_local_html(
        self, parser: WebParser, simple_html_path: Path
    ) -> None:
        """Test parsing a local HTML file."""
        result = await parser.parse_file(simple_html_path)

        assert isinstance(result, ParseResult)
        assert result.success is True
        assert result.error is None
        # Title should be extracted from the h1 or title tag
        assert "Simple Test Article" in result.title
        # Content should include the article text
        assert "Introduction" in result.content or "introduction" in result.content.lower()
        assert "Main Content" in result.content or "main content" in result.content.lower()
        # Metadata should include author
        assert "author" in result.metadata
        assert result.metadata["author"] == "John Doe"

    async def test_parse_invalid_path(self, parser: WebParser) -> None:
        """Test handling of non-existent file."""
        invalid_path = Path("/non/existent/path/to/file.html")
        result = await parser.parse_file(invalid_path)

        assert isinstance(result, ParseResult)
        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower() or "does not exist" in result.error.lower()

    async def test_parse_empty_html(self, parser: WebParser, tmp_path: Path) -> None:
        """Test parsing an empty HTML file."""
        empty_html = tmp_path / "empty.html"
        empty_html.write_text("")

        result = await parser.parse_file(empty_html)

        assert isinstance(result, ParseResult)
        # Empty file should fail with an appropriate error
        assert result.success is False
        assert result.error is not None
        assert "empty" in result.error.lower()

    async def test_parse_html_with_images(
        self, parser: WebParser, tmp_path: Path
    ) -> None:
        """Test extracting image URLs from HTML."""
        html_with_images = tmp_path / "images.html"
        html_with_images.write_text("""
        <!DOCTYPE html>
        <html>
        <head><title>Images Test</title></head>
        <body>
            <article>
                <h1>Article with Images</h1>
                <img src="https://example.com/image1.jpg" alt="Image 1">
                <p>Some text</p>
                <img src="/relative/image2.png" alt="Image 2">
            </article>
        </body>
        </html>
        """)

        result = await parser.parse_file(html_with_images)

        assert result.success is True
        assert len(result.images) >= 1
        assert "https://example.com/image1.jpg" in result.images

    async def test_parse_html_with_description(
        self, parser: WebParser, tmp_path: Path
    ) -> None:
        """Test extracting description metadata from HTML."""
        html_with_desc = tmp_path / "description.html"
        html_with_desc.write_text("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Description Test</title>
            <meta name="description" content="This is a test description.">
        </head>
        <body>
            <article>
                <h1>Article</h1>
                <p>Content here.</p>
            </article>
        </body>
        </html>
        """)

        result = await parser.parse_file(html_with_desc)

        assert result.success is True
        assert "description" in result.metadata
        assert result.metadata["description"] == "This is a test description."

    async def test_parse_malformed_html(self, parser: WebParser, tmp_path: Path) -> None:
        """Test parsing malformed HTML that should still be handled."""
        malformed_html = tmp_path / "malformed.html"
        malformed_html.write_text("""
        <html>
        <head><title>Malformed
        <body>
        <h1>Unclosed tags
        <p>This HTML is not well-formed but should still parse.
        </html>
        """)

        result = await parser.parse_file(malformed_html)

        # Parser should handle malformed HTML gracefully
        assert result.success is True
        assert len(result.content) > 0
