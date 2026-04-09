from __future__ import annotations
"""Ingest service for importing documents from URLs and files."""

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.config import Settings, get_settings
from src.database import Database
from src.parsers.base import ParseResult
from src.parsers.github import GitHubParser
from src.parsers.video import VideoParser
from src.parsers.web import WebParser
from src.parsers.pdf import PDFParser


class IngestResult:
    """Result of an ingest operation.

    Attributes:
        success: Whether the ingest was successful.
        doc_id: Document ID if successful.
        title: Document title.
        path: Storage path in the vault.
        error: Error message if failed.
    """

    def __init__(
        self,
        success: bool,
        doc_id: Optional[str] = None,
        title: Optional[str] = None,
        path: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Initialize the ingest result."""
        self.success = success
        self.doc_id = doc_id
        self.title = title
        self.path = path
        self.error = error

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result = {"success": self.success}
        if self.doc_id:
            result["doc_id"] = self.doc_id
        if self.title:
            result["title"] = self.title
        if self.path:
            result["path"] = self.path
        if self.error:
            result["error"] = self.error
        return result


class IngestService:
    """Service for importing documents from various sources.

    Handles importing content from URLs and local files, saving them
    to the vault and creating database records.
    """

    def __init__(self, db: Database, settings: Optional[Settings] = None) -> None:
        """Initialize the ingest service.

        Args:
            db: Database instance for storing document records.
            settings: Application settings (uses default if not provided).
        """
        self.db = db
        self.settings = settings or get_settings()
        self.vault_path = Path(self.settings.vault_path)
        self.web_parser = WebParser()
        self.pdf_parser = PDFParser()
        self.video_parser = VideoParser()
        self.github_parser = GitHubParser()

    async def ingest_url(
        self,
        url: str,
        tags: Optional[list[str]] = None,
    ) -> IngestResult:
        """Import content from a URL.

        Args:
            url: The URL to import content from.
            tags: Optional list of tags to associate with the document.

        Returns:
            IngestResult with the outcome of the import.
        """
        # Parse the URL
        parse_result = await self.web_parser.parse_url(url)

        if not parse_result.success:
            return IngestResult(success=False, error=parse_result.error)

        # Generate document ID
        doc_id = self._generate_id()

        # Determine storage path
        storage_path = f"raw/web/{doc_id}.md"

        # Save content to file
        await self._save_document(storage_path, parse_result, tags)

        # Create database record
        await self._create_db_record(
            doc_id=doc_id,
            doc_type="web",
            path=storage_path,
            parse_result=parse_result,
            tags=tags,
        )

        return IngestResult(
            success=True,
            doc_id=doc_id,
            title=parse_result.title,
            path=storage_path,
        )

    async def ingest_file(
        self,
        path: str,
        tags: Optional[list[str]] = None,
    ) -> IngestResult:
        """Import content from a local file.

        Args:
            path: Path to the local file to import.
            tags: Optional list of tags to associate with the document.

        Returns:
            IngestResult with the outcome of the import.
        """
        file_path = Path(path)

        # Check if file exists
        if not file_path.exists():
            return IngestResult(success=False, error=f"File not found: {path}")

        if not file_path.is_file():
            return IngestResult(success=False, error=f"Path is not a file: {path}")

        # Determine file type and select parser
        parse_result: ParseResult
        doc_type: str

        suffix = file_path.suffix.lower()
        if suffix == ".pdf":
            parse_result = await self.pdf_parser.parse_file(file_path)
            doc_type = "paper"
        elif suffix in (".html", ".htm"):
            parse_result = await self.web_parser.parse_file(file_path)
            doc_type = "web"
        else:
            # Default to web parser for text files
            parse_result = await self.web_parser.parse_file(file_path)
            doc_type = "web"

        if not parse_result.success:
            return IngestResult(success=False, error=parse_result.error)

        # Generate document ID
        doc_id = self._generate_id()

        # Determine storage path based on type
        type_dir = "papers" if doc_type == "paper" else "web"
        storage_path = f"raw/{type_dir}/{doc_id}.md"

        # Save content to file
        await self._save_document(storage_path, parse_result, tags)

        # Create database record
        await self._create_db_record(
            doc_id=doc_id,
            doc_type=doc_type,
            path=storage_path,
            parse_result=parse_result,
            tags=tags,
        )

        return IngestResult(
            success=True,
            doc_id=doc_id,
            title=parse_result.title,
            path=storage_path,
        )

    async def ingest_video(
        self,
        url: str,
        tags: Optional[list[str]] = None,
    ) -> IngestResult:
        """Import content from a video URL.

        Args:
            url: The video URL (YouTube or Bilibili).
            tags: Optional list of tags.

        Returns:
            IngestResult with the outcome of the import.
        """
        parse_result = await self.video_parser.parse_url(url)

        if not parse_result.success:
            return IngestResult(success=False, error=parse_result.error)

        doc_id = self._generate_id()
        storage_path = f"raw/videos/{doc_id}.md"

        await self._save_document(storage_path, parse_result, tags)
        await self._create_db_record(
            doc_id=doc_id,
            doc_type="video",
            path=storage_path,
            parse_result=parse_result,
            tags=tags,
        )

        return IngestResult(
            success=True,
            doc_id=doc_id,
            title=parse_result.title,
            path=storage_path,
        )

    async def ingest_github(
        self,
        repo_url: str,
        tags: Optional[list[str]] = None,
    ) -> IngestResult:
        """Import content from a GitHub repository.

        Args:
            repo_url: The GitHub repository URL.
            tags: Optional list of tags.

        Returns:
            IngestResult with the outcome of the import.
        """
        parse_result = await self.github_parser.parse_url(repo_url)

        if not parse_result.success:
            return IngestResult(success=False, error=parse_result.error)

        doc_id = self._generate_id()
        storage_path = f"raw/code/{doc_id}.md"

        await self._save_document(storage_path, parse_result, tags)
        await self._create_db_record(
            doc_id=doc_id,
            doc_type="code",
            path=storage_path,
            parse_result=parse_result,
            tags=tags,
        )

        return IngestResult(
            success=True,
            doc_id=doc_id,
            title=parse_result.title,
            path=storage_path,
        )

    def _generate_id(self) -> str:
        """Generate a unique document ID.

        Returns:
            UUID-based document ID.
        """
        return str(uuid.uuid4())

    async def _save_document(
        self,
        storage_path: str,
        parse_result: ParseResult,
        tags: Optional[list[str]] = None,
    ) -> None:
        """Save parsed content to the vault.

        Args:
            storage_path: Relative path within the vault.
            parse_result: Parsed content to save.
            tags: Optional list of tags.
        """
        full_path = self.vault_path / storage_path

        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Build markdown content
        content = self._build_markdown(parse_result, tags)

        # Write to file
        full_path.write_text(content, encoding="utf-8")

    def _build_markdown(
        self,
        parse_result: ParseResult,
        tags: Optional[list[str]] = None,
    ) -> str:
        """Build markdown content from parse result.

        Args:
            parse_result: Parsed content.
            tags: Optional list of tags.

        Returns:
            Formatted markdown string.
        """
        lines: list[str] = []

        # Front matter
        lines.append("---")
        lines.append(f"title: {parse_result.title or 'Untitled'}")

        # Add source URL if available
        if parse_result.metadata.get("source_url"):
            lines.append(f"source: {parse_result.metadata['source_url']}")

        # Add tags
        if tags:
            lines.append(f"tags: [{', '.join(tags)}]")

        # Add metadata
        if parse_result.metadata.get("author"):
            lines.append(f"author: {parse_result.metadata['author']}")

        lines.append("---")
        lines.append("")

        # Title
        lines.append(f"# {parse_result.title or 'Untitled'}")
        lines.append("")

        # Content
        lines.append(parse_result.content)

        return "\n".join(lines)

    async def _create_db_record(
        self,
        doc_id: str,
        doc_type: str,
        path: str,
        parse_result: ParseResult,
        tags: Optional[list[str]] = None,
    ) -> None:
        """Create a database record for the document.

        Args:
            doc_id: Document ID.
            doc_type: Document type (web, paper, etc.).
            path: Storage path.
            parse_result: Parsed content.
            tags: Optional list of tags.
        """
        # Merge tags into metadata
        metadata = dict(parse_result.metadata)
        if tags:
            metadata["tags"] = tags

        await self.db.create_document(
            doc_id=doc_id,
            doc_type=doc_type,
            path=path,
            title=parse_result.title,
            status="pending",
            metadata=metadata,
        )
