from __future__ import annotations
"""PDF parser using PyMuPDF (fitz) for text and metadata extraction."""

from dataclasses import dataclass
from pathlib import Path

import fitz  # PyMuPDF

from src.parsers.base import BaseParser, ParseResult


@dataclass
class PDFMetadata:
    """Extracted PDF metadata.

    Attributes:
        title: Document title.
        author: Document author.
        page_count: Total number of pages.
        creation_date: Document creation date.
    """

    title: str = ""
    author: str = ""
    page_count: int = 0
    creation_date: str = ""


class PDFParser(BaseParser):
    """Parser for PDF documents.

    Uses PyMuPDF (fitz) for PDF parsing, extracting text content and metadata.
    """

    async def parse_file(self, path: Path) -> ParseResult:
        """Parse content from a PDF file.

        Args:
            path: Path to the PDF file to parse.

        Returns:
            ParseResult with the extracted content and metadata.
        """
        # Check if file exists
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
            # Open the PDF document
            doc = fitz.open(path)
        except fitz.FileDataError as e:
            return ParseResult(
                success=False,
                error=f"Invalid PDF format: {str(e)}",
            )
        except Exception as e:
            return ParseResult(
                success=False,
                error=f"Failed to open PDF: {str(e)}",
            )

        try:
            # Check if the PDF is encrypted
            if doc.is_encrypted:
                return ParseResult(
                    success=False,
                    error="PDF is encrypted and cannot be parsed",
                )

            # Extract metadata
            metadata = self._extract_metadata(doc)

            # Extract text from all pages
            content = self._extract_text(doc)

            return ParseResult(
                success=True,
                title=metadata.title,
                content=content,
                metadata={
                    "author": metadata.author,
                    "page_count": metadata.page_count,
                    "creation_date": metadata.creation_date,
                },
            )
        finally:
            doc.close()

    def _extract_metadata(self, doc: fitz.Document) -> PDFMetadata:
        """Extract metadata from the PDF document.

        Args:
            doc: The PyMuPDF Document object.

        Returns:
            PDFMetadata with extracted information.
        """
        pdf_metadata = doc.metadata or {}

        # Extract title, fallback to "Untitled" if not present
        title = pdf_metadata.get("title", "") or "Untitled"

        # Extract author
        author = pdf_metadata.get("author", "") or ""

        # Extract creation date and format it
        creation_date_raw = pdf_metadata.get("creationDate", "") or ""
        creation_date = self._format_pdf_date(creation_date_raw)

        return PDFMetadata(
            title=title,
            author=author,
            page_count=doc.page_count,
            creation_date=creation_date,
        )

    def _extract_text(self, doc: fitz.Document) -> str:
        """Extract text from all pages of the PDF document.

        Args:
            doc: The PyMuPDF Document object.

        Returns:
            Combined text from all pages.
        """
        text_parts: list[str] = []

        for page in doc:
            page_text = page.get_text()
            # Only add non-empty text after stripping
            stripped_text = page_text.strip()
            if stripped_text:
                text_parts.append(stripped_text)

        return "\n\n".join(text_parts)

    def _format_pdf_date(self, date_str: str) -> str:
        """Format a PDF date string to a more readable format.

        PDF dates are in format: D:YYYYMMDDHHmmSSOHH'mm'
        Example: D:20240115000000Z

        Args:
            date_str: The raw PDF date string.

        Returns:
            Formatted date string or empty string if invalid.
        """
        if not date_str:
            return ""

        # Remove the "D:" prefix if present
        if date_str.startswith("D:"):
            date_str = date_str[2:]

        # Extract just the date portion (YYYYMMDD)
        if len(date_str) >= 8:
            year = date_str[0:4]
            month = date_str[4:6]
            day = date_str[6:8]
            return f"{year}-{month}-{day}"

        return date_str
