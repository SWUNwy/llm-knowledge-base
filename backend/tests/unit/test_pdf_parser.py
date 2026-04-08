"""Tests for the PDF parser module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.parsers.base import ParseResult
from src.parsers.pdf import PDFParser


class TestPDFParser:
    """Tests for PDFParser class."""

    @pytest.fixture
    def parser(self) -> PDFParser:
        """Create a PDFParser instance."""
        return PDFParser()

    async def test_parse_pdf_file_not_found(self, parser: PDFParser) -> None:
        """Test handling of missing file."""
        invalid_path = Path("/non/existent/path/to/file.pdf")
        result = await parser.parse_file(invalid_path)

        assert isinstance(result, ParseResult)
        assert result.success is False
        assert result.error is not None
        assert "not found" in result.error.lower()

    async def test_parse_pdf_invalid_format(self, parser: PDFParser, tmp_path: Path) -> None:
        """Test handling of non-PDF file."""
        # Create a text file (not a valid PDF)
        invalid_file = tmp_path / "invalid.pdf"
        invalid_file.write_text("This is not a PDF file")

        result = await parser.parse_file(invalid_file)

        assert isinstance(result, ParseResult)
        assert result.success is False
        assert result.error is not None
        assert "invalid" in result.error.lower() or "not a pdf" in result.error.lower()

    async def test_parse_pdf_encrypted(self, parser: PDFParser, tmp_path: Path) -> None:
        """Test handling of encrypted PDF."""
        # Mock PyMuPDF to simulate an encrypted PDF
        with patch("src.parsers.pdf.fitz") as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.is_encrypted = True
            mock_fitz.open.return_value = mock_doc

            # Create a dummy PDF file
            encrypted_pdf = tmp_path / "encrypted.pdf"
            encrypted_pdf.write_bytes(b"%PDF-1.4\ndummy content")

            result = await parser.parse_file(encrypted_pdf)

            assert isinstance(result, ParseResult)
            assert result.success is False
            assert result.error is not None
            assert "encrypted" in result.error.lower()

    async def test_parse_pdf_success(self, parser: PDFParser, tmp_path: Path) -> None:
        """Test successful PDF parsing."""
        # Mock PyMuPDF to simulate a valid PDF
        with patch("src.parsers.pdf.fitz") as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.is_encrypted = False
            mock_doc.page_count = 2
            mock_doc.metadata = {
                "title": "Test Document",
                "author": "Test Author",
                "creationDate": "D:20240115000000Z",
            }

            # Mock pages
            mock_page1 = MagicMock()
            mock_page1.get_text.return_value = "Page 1 content"
            mock_page2 = MagicMock()
            mock_page2.get_text.return_value = "Page 2 content"

            mock_doc.__getitem__ = lambda _, idx: [mock_page1, mock_page2][idx]
            mock_doc.__len__ = lambda _: 2
            mock_doc.__iter__ = lambda _: iter([mock_page1, mock_page2])

            mock_fitz.open.return_value = mock_doc

            # Create a dummy PDF file
            pdf_file = tmp_path / "test.pdf"
            pdf_file.write_bytes(b"%PDF-1.4\ndummy content")

            result = await parser.parse_file(pdf_file)

            assert isinstance(result, ParseResult)
            assert result.success is True
            assert result.error is None
            assert result.title == "Test Document"
            assert "Page 1 content" in result.content
            assert "Page 2 content" in result.content
            assert result.metadata["author"] == "Test Author"
            assert result.metadata["page_count"] == 2
            assert "creation_date" in result.metadata

    async def test_parse_pdf_no_metadata(self, parser: PDFParser, tmp_path: Path) -> None:
        """Test PDF parsing with no metadata."""
        with patch("src.parsers.pdf.fitz") as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.is_encrypted = False
            mock_doc.page_count = 1
            mock_doc.metadata = {}

            mock_page = MagicMock()
            mock_page.get_text.return_value = "Some content"
            mock_doc.__iter__ = lambda _: iter([mock_page])

            mock_fitz.open.return_value = mock_doc

            pdf_file = tmp_path / "no_metadata.pdf"
            pdf_file.write_bytes(b"%PDF-1.4\ndummy content")

            result = await parser.parse_file(pdf_file)

            assert result.success is True
            assert result.title == "Untitled"
            assert result.metadata["author"] == ""

    async def test_parse_pdf_empty_pages(self, parser: PDFParser, tmp_path: Path) -> None:
        """Test PDF parsing with empty pages."""
        with patch("src.parsers.pdf.fitz") as mock_fitz:
            mock_doc = MagicMock()
            mock_doc.is_encrypted = False
            mock_doc.page_count = 1
            mock_doc.metadata = {"title": "Empty PDF"}

            mock_page = MagicMock()
            mock_page.get_text.return_value = "   \n\n   "  # Whitespace only
            mock_doc.__iter__ = lambda _: iter([mock_page])

            mock_fitz.open.return_value = mock_doc

            pdf_file = tmp_path / "empty.pdf"
            pdf_file.write_bytes(b"%PDF-1.4\ndummy content")

            result = await parser.parse_file(pdf_file)

            assert result.success is True
            assert result.content == ""
