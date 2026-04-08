"""Compile service for converting raw documents into wiki articles."""

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from src.config import Settings, get_settings
from src.database import Database
from src.llm.client import LLMClient
from src.llm.prompts import PromptTemplates
from src.repositories.document_repo import DocumentRepo

logger = logging.getLogger(__name__)


@dataclass
class CompileResult:
    """Result of compiling a single document.

    Attributes:
        success: Whether the compilation was successful.
        doc_id: Document ID.
        wiki_path: Path to the generated wiki article.
        title: Document title.
        error: Error message if compilation failed.
    """

    success: bool
    doc_id: str = ""
    wiki_path: str = ""
    title: str = ""
    error: str = ""

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result: dict = {"success": self.success, "doc_id": self.doc_id}
        if self.wiki_path:
            result["wiki_path"] = self.wiki_path
        if self.title:
            result["title"] = self.title
        if self.error:
            result["error"] = self.error
        return result


@dataclass
class CompileBatchResult:
    """Result of a batch compilation.

    Attributes:
        task_id: Task ID for async batches, empty for sync batches.
        total: Total number of documents to compile.
        completed: Number of successfully compiled documents.
        failed: Number of failed compilations.
        results: List of individual compile results (sync mode only).
        status: Overall status of the batch.
    """

    task_id: str = ""
    total: int = 0
    completed: int = 0
    failed: int = 0
    results: list[CompileResult] = field(default_factory=list)
    status: str = "pending"

    def to_dict(self) -> dict:
        """Convert to dictionary for API response."""
        result: dict = {
            "total": self.total,
            "completed": self.completed,
            "failed": self.failed,
            "status": self.status,
        }
        if self.task_id:
            result["task_id"] = self.task_id
        if self.results:
            result["results"] = [r.to_dict() for r in self.results]
        return result


class CompileService:
    """Service for compiling raw documents into wiki articles.

    Reads raw documents from the vault, sends them to an LLM for
    processing, and generates structured wiki articles with [[wiki-links]].
    """

    def __init__(
        self,
        vault_path: Path,
        doc_repo: DocumentRepo,
        llm_client: LLMClient,
        settings: Optional[Settings] = None,
    ) -> None:
        """Initialize the compile service.

        Args:
            vault_path: Path to the vault root directory.
            doc_repo: Document repository for database operations.
            llm_client: LLM client for generating wiki articles.
            settings: Application settings (uses default if not provided).
        """
        self.vault_path = vault_path
        self.doc_repo = doc_repo
        self.llm_client = llm_client
        self.settings = settings or get_settings()
        self.db = doc_repo.db

    async def compile_document(
        self,
        doc_id: str,
        output_language: str = "中文",
    ) -> CompileResult:
        """Compile a single document into a wiki article.

        Reads the raw document, sends it to the LLM for processing,
        saves the generated wiki article, and updates the document status.

        Args:
            doc_id: ID of the document to compile.
            output_language: Language for the generated wiki article.

        Returns:
            CompileResult with the outcome of the compilation.
        """
        # 1. Get document from repo
        doc = await self.doc_repo.get_document(doc_id)
        if doc is None:
            return CompileResult(
                success=False,
                doc_id=doc_id,
                error=f"Document not found: {doc_id}",
            )

        # 2. Read raw document content from vault
        raw_path = self.vault_path / doc["path"]
        if not raw_path.exists():
            return CompileResult(
                success=False,
                doc_id=doc_id,
                error=f"Raw file not found: {doc['path']}",
            )

        try:
            raw_content = raw_path.read_text(encoding="utf-8")
        except Exception as e:
            return CompileResult(
                success=False,
                doc_id=doc_id,
                error=f"Failed to read document: {e}",
            )

        # 3. Build compile prompt using PromptTemplates
        title = doc.get("title") or "Untitled"
        doc_type = doc.get("type", "web")
        source = doc.get("metadata", {}).get("source_url", "")
        source_id = doc_id

        prompt = PromptTemplates.compile_document(
            title=title,
            type=doc_type,
            source=source,
            content=raw_content,
            source_id=source_id,
            original_title=title,
            output_language=output_language,
        )

        # 4. Call LLM to generate wiki article
        try:
            wiki_content = await self.llm_client.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=4000,
            )
        except Exception as e:
            logger.error(f"LLM generation failed for doc {doc_id}: {e}")
            return CompileResult(
                success=False,
                doc_id=doc_id,
                error=f"LLM generation failed: {e}",
            )

        # 5. Save wiki article to vault/wiki/sources/{id}.md
        wiki_path = f"wiki/sources/{doc_id}.md"
        full_wiki_path = self.vault_path / wiki_path
        full_wiki_path.parent.mkdir(parents=True, exist_ok=True)

        # Build the final wiki markdown with frontmatter
        wiki_markdown = self._build_wiki_markdown(
            doc_id=doc_id,
            title=title,
            wiki_content=wiki_content,
            source_id=source_id,
        )
        full_wiki_path.write_text(wiki_markdown, encoding="utf-8")

        # 6. Update document status to 'processed'
        await self.db.update_document_status(
            doc_id=doc_id,
            status="processed",
            metadata={
                **doc.get("metadata", {}),
                "wiki_path": wiki_path,
                "compiled_at": datetime.now(timezone.utc).isoformat(),
            },
        )

        logger.info(f"Successfully compiled document {doc_id}")
        return CompileResult(
            success=True,
            doc_id=doc_id,
            wiki_path=wiki_path,
            title=title,
        )

    async def compile_batch(
        self,
        doc_ids: list[str],
        output_language: str = "中文",
    ) -> CompileBatchResult:
        """Compile a batch of documents.

        For 5 or fewer documents, compiles synchronously and returns
        results directly. For more than 5, creates an async task.

        Args:
            doc_ids: List of document IDs to compile.
            output_language: Language for generated wiki articles.

        Returns:
            CompileBatchResult with either direct results or a task_id.
        """
        total = len(doc_ids)

        if total <= 5:
            # Synchronous mode: compile all and return results
            return await self._compile_sync(doc_ids, output_language)
        else:
            # Async mode: create task and return task_id
            task_id = f"compile-{uuid.uuid4().hex[:12]}"
            await self.db.create_compile_task(
                task_id=task_id,
                total_docs=total,
            )

            # Start background processing
            import asyncio
            asyncio.create_task(
                self._compile_async(task_id, doc_ids, output_language)
            )

            return CompileBatchResult(
                task_id=task_id,
                total=total,
                status="pending",
            )

    async def get_task_status(self, task_id: str) -> Optional[dict]:
        """Get the status of an async compile task.

        Args:
            task_id: The task ID to look up.

        Returns:
            Task status dict or None if task not found.
        """
        return await self.db.get_compile_task(task_id)

    async def _compile_sync(
        self,
        doc_ids: list[str],
        output_language: str,
    ) -> CompileBatchResult:
        """Compile documents synchronously.

        Args:
            doc_ids: List of document IDs.
            output_language: Language for wiki articles.

        Returns:
            CompileBatchResult with all individual results.
        """
        results: list[CompileResult] = []
        completed = 0
        failed = 0

        for doc_id in doc_ids:
            result = await self.compile_document(doc_id, output_language)
            results.append(result)
            if result.success:
                completed += 1
            else:
                failed += 1

        return CompileBatchResult(
            total=len(doc_ids),
            completed=completed,
            failed=failed,
            results=results,
            status="completed",
        )

    async def _compile_async(
        self,
        task_id: str,
        doc_ids: list[str],
        output_language: str,
    ) -> None:
        """Compile documents asynchronously, updating task progress.

        Args:
            task_id: Task ID for progress tracking.
            doc_ids: List of document IDs.
            output_language: Language for wiki articles.
        """
        completed = 0
        failed = 0

        try:
            for doc_id in doc_ids:
                result = await self.compile_document(doc_id, output_language)
                if result.success:
                    completed += 1
                else:
                    failed += 1

                # Update task progress
                await self.db.update_compile_task(
                    task_id=task_id,
                    completed_docs=completed,
                    failed_docs=failed,
                )

            # Mark task as completed
            result_data = json.dumps({
                "total": len(doc_ids),
                "completed": completed,
                "failed": failed,
            })
            await self.db.update_compile_task(
                task_id=task_id,
                status="completed",
                result=result_data,
            )
        except Exception as e:
            logger.error(f"Async compile task {task_id} failed: {e}")
            await self.db.update_compile_task(
                task_id=task_id,
                status="failed",
                result=json.dumps({"error": str(e)}),
            )

    def _build_wiki_markdown(
        self,
        doc_id: str,
        title: str,
        wiki_content: str,
        source_id: str,
    ) -> str:
        """Build the final wiki markdown with frontmatter.

        Args:
            doc_id: Document ID.
            title: Document title.
            wiki_content: LLM-generated wiki content.
            source_id: Source document ID.

        Returns:
            Complete wiki markdown string with frontmatter.
        """
        lines: list[str] = []
        lines.append("---")
        lines.append(f"id: {doc_id}")
        lines.append(f"title: {title}")
        lines.append(f"source: {source_id}")
        lines.append(f"compiled_at: {datetime.now(timezone.utc).isoformat()}")
        lines.append("---")
        lines.append("")
        lines.append(wiki_content)
        return "\n".join(lines)
