"""Parser base classes and data structures."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional


@dataclass
class ParseResult:
    """Result of a parsing operation.

    Attributes:
        success: Whether the parsing was successful.
        title: Extracted title of the document.
        content: Extracted main content as plain text.
        metadata: Additional metadata extracted from the source.
        images: List of image URLs found in the document.
        error: Error message if parsing failed.
    """

    success: bool
    title: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    images: list[str] = field(default_factory=list)
    error: Optional[str] = None


class BaseParser:
    """Base class for all content parsers.

    Provides a common interface for parsing content from URLs and local files.
    Subclasses should implement at least one of parse_url or parse_file.
    """

    async def parse_url(self, url: str) -> ParseResult:
        """Parse content from a URL.

        Args:
            url: The URL to fetch and parse.

        Returns:
            ParseResult with the extracted content.

        Raises:
            NotImplementedError: If the subclass does not support URL parsing.
        """
        raise NotImplementedError("Subclasses must implement parse_url")

    async def parse_file(self, path: Path) -> ParseResult:
        """Parse content from a local file.

        Args:
            path: Path to the local file to parse.

        Returns:
            ParseResult with the extracted content.

        Raises:
            NotImplementedError: If the subclass does not support file parsing.
        """
        raise NotImplementedError("Subclasses must implement parse_file")
