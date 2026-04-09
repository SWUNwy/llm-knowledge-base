from __future__ import annotations
"""Indexer service for managing full-text search indexes."""

from src.database import Database
from src.repositories.document_repo import DocumentRepo


class Indexer:
    """Service for managing document indexes.

    Handles FTS indexing and search operations.
    """

    def __init__(self, db: Database) -> None:
        """Initialize the indexer.

        Args:
            db: Database instance.
        """
        self.db = db
        self.doc_repo = DocumentRepo(db)

    async def index_document(self, doc_id: str, content: str, title: str) -> None:
        """Index a document for full-text search.

        Args:
            doc_id: Document ID.
            content: Document content to index.
            title: Document title.
        """
        await self.db.index_document_content(doc_id=doc_id, title=title, content=content)

    async def search(
        self,
        query: str,
        limit: int = 10,
    ) -> list[dict]:
        """Search documents using full-text search.

        Args:
            query: Search query string.
            limit: Maximum results to return.

        Returns:
            List of search results with relevance scores.
        """
        return await self.doc_repo.search(query=query, limit=limit)

    async def remove_document(self, doc_id: str) -> None:
        """Remove a document from the search index.

        Args:
            doc_id: Document ID to remove.
        """
        await self.db._conn.execute(
            "DELETE FROM documents_fts WHERE id = ?",
            (doc_id,),
        )
        await self.db._conn.commit()
