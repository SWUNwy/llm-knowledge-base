from __future__ import annotations
"""Unified file parser using Microsoft MarkItDown library."""

import asyncio
import logging
from pathlib import Path
from typing import Optional

from src.parsers.base import BaseParser, ParseResult

logger = logging.getLogger(__name__)


class MarkItDownParser(BaseParser):
    """Unified parser for multiple file formats via MarkItDown.

    Converts PDF, DOCX, PPTX, XLSX, HTML, EPUB, CSV, images, and more
    to structured Markdown. Replaces the previous PDFParser and WebParser.
    """

    SUPPORTED_EXTENSIONS = {
        ".pdf", ".docx", ".pptx", ".xlsx", ".xls",
        ".html", ".htm", ".epub", ".csv",
        ".jpg", ".jpeg", ".png", ".ipynb", ".zip",
    }

    def __init__(
        self,
        llm_client: Optional[object] = None,
        llm_model: Optional[str] = None,
    ) -> None:
        from markitdown import MarkItDown

        kwargs = {}
        if llm_client is not None:
            kwargs["llm_client"] = llm_client
        if llm_model is not None:
            kwargs["llm_model"] = llm_model

        self._md = MarkItDown(**kwargs)

    async def parse_file(self, path: Path) -> ParseResult:
        if not path.exists():
            return ParseResult(success=False, error=f"File not found: {path}")

        if not path.is_file():
            return ParseResult(success=False, error=f"Path is not a file: {path}")

        suffix = path.suffix.lower()
        if suffix not in self.SUPPORTED_EXTENSIONS:
            return ParseResult(
                success=False,
                error=f"Unsupported file format: {suffix}. Supported: {', '.join(sorted(self.SUPPORTED_EXTENSIONS))}",
            )

        try:
            result = await asyncio.to_thread(self._md.convert, str(path))
            return ParseResult(
                success=True,
                title=result.title or "",
                content=result.markdown,
                metadata={"source_format": suffix.lstrip(".")},
            )
        except Exception as e:
            logger.error("MarkItDown failed to parse %s: %s", path, e)
            return ParseResult(success=False, error=f"Failed to parse {path}: {str(e)}")

    async def parse_url(self, url: str) -> ParseResult:
        try:
            result = await asyncio.to_thread(self._md.convert, url)
            return ParseResult(
                success=True,
                title=result.title or "",
                content=result.markdown,
                metadata={
                    "source_format": "html",
                    "source_url": url,
                },
            )
        except Exception as e:
            logger.error("MarkItDown failed to parse URL %s: %s", url, e)
            return ParseResult(success=False, error=f"Failed to parse URL: {str(e)}")
