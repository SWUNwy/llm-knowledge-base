"""Tests for MarkItDownParser."""

import asyncio
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.parsers.base import ParseResult
from src.parsers.markitdown import MarkItDownParser


class TestMarkItDownParser:
    """Tests for MarkItDownParser class."""

    @pytest.fixture
    def parser(self) -> MarkItDownParser:
        return MarkItDownParser()

    def test_supported_extensions(self, parser: MarkItDownParser) -> None:
        assert ".pdf" in MarkItDownParser.SUPPORTED_EXTENSIONS
        assert ".docx" in MarkItDownParser.SUPPORTED_EXTENSIONS
        assert ".pptx" in MarkItDownParser.SUPPORTED_EXTENSIONS
        assert ".xlsx" in MarkItDownParser.SUPPORTED_EXTENSIONS
        assert ".html" in MarkItDownParser.SUPPORTED_EXTENSIONS
        assert ".epub" in MarkItDownParser.SUPPORTED_EXTENSIONS
        assert ".csv" in MarkItDownParser.SUPPORTED_EXTENSIONS

    @pytest.mark.asyncio
    async def test_parse_file_not_found(self, parser: MarkItDownParser) -> None:
        result = await parser.parse_file(Path("/non/existent/file.pdf"))

        assert isinstance(result, ParseResult)
        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_parse_file_returns_markdown(self, parser: MarkItDownParser, tmp_path: Path) -> None:
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("Name,Age\nAlice,30\nBob,25\n")

        result = await parser.parse_file(csv_file)

        assert result.success is True
        assert result.content
        assert "|" in result.content
        assert result.metadata.get("source_format") == "csv"

    @pytest.mark.asyncio
    async def test_parse_file_sets_source_format(self, parser: MarkItDownParser, tmp_path: Path) -> None:
        csv_file = tmp_path / "data.csv"
        csv_file.write_text("Col1,Col2\nA,B\n")

        result = await parser.parse_file(csv_file)

        assert result.success is True
        assert result.metadata["source_format"] == "csv"

    @pytest.mark.asyncio
    async def test_parse_file_unsupported_format(self, parser: MarkItDownParser, tmp_path: Path) -> None:
        xyz_file = tmp_path / "test.xyz"
        xyz_file.write_text("some content")

        result = await parser.parse_file(xyz_file)

        assert result.success is False
        assert "unsupported" in result.error.lower()

    @pytest.mark.asyncio
    async def test_parse_url_returns_markdown(self, parser: MarkItDownParser) -> None:
        mock_result = MagicMock()
        mock_result.title = "Test Page"
        mock_result.markdown = "# Test Page\n\nSome content"

        with patch.object(parser, "_md") as mock_md:
            mock_md.convert.return_value = mock_result
            result = await parser.parse_url("https://example.com/page.html")

        assert result.success is True
        assert result.title == "Test Page"
        assert result.content == "# Test Page\n\nSome content"
        assert result.metadata["source_format"] == "html"
        assert result.metadata["source_url"] == "https://example.com/page.html"

    @pytest.mark.asyncio
    async def test_parse_url_failure(self, parser: MarkItDownParser) -> None:
        with patch.object(parser, "_md") as mock_md:
            mock_md.convert.side_effect = Exception("Network error")

            result = await parser.parse_url("https://example.com/nonexistent")

        assert result.success is False
        assert result.error is not None

    @pytest.mark.asyncio
    async def test_parse_file_with_mock(self, parser: MarkItDownParser, tmp_path: Path) -> None:
        mock_result = MagicMock()
        mock_result.title = "Mock PDF Title"
        mock_result.markdown = "# Mock PDF\n\nContent with **bold** and a table:\n\n| A | B |\n|---|---|\n| 1 | 2 |"

        with patch.object(parser, "_md") as mock_md:
            mock_md.convert.return_value = mock_result
            pdf_file = tmp_path / "test.pdf"
            pdf_file.write_bytes(b"%PDF-1.4 dummy")

            result = await parser.parse_file(pdf_file)

        assert result.success is True
        assert result.title == "Mock PDF Title"
        assert "| A | B |" in result.content
        assert result.metadata["source_format"] == "pdf"

    @pytest.mark.asyncio
    async def test_parse_file_no_title(self, parser: MarkItDownParser, tmp_path: Path) -> None:
        mock_result = MagicMock()
        mock_result.title = None
        mock_result.markdown = "Just content"

        with patch.object(parser, "_md") as mock_md:
            mock_md.convert.return_value = mock_result
            csv_file = tmp_path / "test.csv"
            csv_file.write_text("A\n1\n")

            result = await parser.parse_file(csv_file)

        assert result.success is True
        assert result.title == ""
