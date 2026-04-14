from __future__ import annotations
"""Ingest service for importing documents from URLs and files."""

import uuid
from pathlib import Path
from typing import Optional

from src.config import Settings, get_settings
from src.database import Database
from src.parsers.base import ParseResult
from src.parsers.github import GitHubParser
from src.parsers.markitdown import MarkItDownParser
from src.parsers.video import VideoParser
from src.services.processor import DocumentProcessor


# Maps file extension to doc_type for database categorization
DOC_TYPE_MAP: dict[str, str] = {
    ".pdf": "paper",
    ".docx": "paper",
    ".pptx": "presentation",
    ".xlsx": "data",
    ".xls": "data",
    ".csv": "data",
    ".epub": "book",
    ".html": "web",
    ".htm": "web",
    ".jpg": "image",
    ".jpeg": "image",
    ".png": "image",
    ".ipynb": "code",
    ".zip": "archive",
}


class IngestResult:
    """Result of an ingest operation."""

    def __init__(
        self,
        success: bool,
        doc_id: Optional[str] = None,
        title: Optional[str] = None,
        path: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        self.success = success
        self.doc_id = doc_id
        self.title = title
        self.path = path
        self.error = error

    def to_dict(self) -> dict:
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

    Routes to the correct pipeline (document/video/code) based on input,
    processes through the DocumentProcessor pipeline, and persists results.
    """

    def __init__(self, db: Database, settings: Optional[Settings] = None) -> None:
        self.db = db
        self.settings = settings or get_settings()
        self.vault_path = Path(self.settings.vault_path)
        self.markdown_parser = MarkItDownParser()
        self.video_parser = VideoParser()
        self.github_parser = GitHubParser()
        self.processor = DocumentProcessor(
            chunk_token_limit=self.settings.chunk_token_limit,
        )

    async def ingest_url(
        self,
        url: str,
        tags: Optional[list[str]] = None,
    ) -> IngestResult:
        parse_result = await self.markdown_parser.parse_url(url)

        if not parse_result.success:
            return IngestResult(success=False, error=parse_result.error)

        doc_id = self._generate_id()
        storage_path = f"raw/web/{doc_id}.md"

        await self._save_document(storage_path, parse_result, tags)
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
        file_path = Path(path)

        if not file_path.exists():
            return IngestResult(success=False, error=f"File not found: {path}")

        if not file_path.is_file():
            return IngestResult(success=False, error=f"Path is not a file: {path}")

        suffix = file_path.suffix.lower()
        doc_type = DOC_TYPE_MAP.get(suffix, "web")

        parse_result = await self.markdown_parser.parse_file(file_path)

        if not parse_result.success:
            return IngestResult(success=False, error=parse_result.error)

        doc_id = self._generate_id()
        type_dir = self._type_to_dir(doc_type)
        storage_path = f"raw/{type_dir}/{doc_id}.md"

        await self._save_document(storage_path, parse_result, tags)
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
        return str(uuid.uuid4())

    def _type_to_dir(self, doc_type: str) -> str:
        mapping = {
            "paper": "papers",
            "presentation": "papers",
            "data": "papers",
            "book": "papers",
            "image": "papers",
            "web": "web",
            "code": "code",
            "archive": "papers",
        }
        return mapping.get(doc_type, "web")

    async def _save_document(
        self,
        storage_path: str,
        parse_result: ParseResult,
        tags: Optional[list[str]] = None,
    ) -> None:
        full_path = self.vault_path / storage_path
        full_path.parent.mkdir(parents=True, exist_ok=True)

        content = self._build_markdown(parse_result, tags)
        full_path.write_text(content, encoding="utf-8")

    def _build_markdown(
        self,
        parse_result: ParseResult,
        tags: Optional[list[str]] = None,
    ) -> str:
        lines: list[str] = []

        lines.append("---")
        lines.append(f"title: {parse_result.title or 'Untitled'}")

        if parse_result.metadata.get("source_url"):
            lines.append(f"source: {parse_result.metadata['source_url']}")

        if parse_result.metadata.get("source_format"):
            lines.append(f"format: {parse_result.metadata['source_format']}")

        if tags:
            lines.append(f"tags: [{', '.join(tags)}]")

        if parse_result.metadata.get("author"):
            lines.append(f"author: {parse_result.metadata['author']}")

        lines.append("---")
        lines.append("")
        lines.append(f"# {parse_result.title or 'Untitled'}")
        lines.append("")
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
