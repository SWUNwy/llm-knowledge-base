from __future__ import annotations
"""Document repository for database operations."""

from typing import Optional

from src.database import Database


class DocumentRepo:
    """Repository for document CRUD and search operations.

    Wraps Database methods to provide a clean interface for the
    document router layer.
    """

    def __init__(self, db: Database) -> None:
        """Initialize with a database instance.

        Args:
            db: Database connection instance.
        """
        self.db = db

    async def list_documents(
        self,
        doc_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        """List documents with optional filters and pagination.

        Args:
            doc_type: Filter by document type (web, paper, video, code).
            status: Filter by status (pending, processed).
            limit: Maximum number of results.
            offset: Number of results to skip.

        Returns:
            Tuple of (list of document dicts, total count).
        """
        conditions: list[str] = []
        params: list[str] = []

        if doc_type is not None:
            conditions.append("type = ?")
            params.append(doc_type)

        if status is not None:
            conditions.append("status = ?")
            params.append(status)

        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        # Get total count
        count_sql = f"SELECT COUNT(*) FROM documents {where_clause}"
        async with self.db._conn.execute(count_sql, params) as cursor:
            row = await cursor.fetchone()
            total = row[0] if row else 0

        # Get paginated results
        query_sql = (
            f"SELECT * FROM documents {where_clause} "
            "ORDER BY created_at DESC LIMIT ? OFFSET ?"
        )
        async with self.db._conn.execute(
            query_sql, params + [str(limit), str(offset)]
        ) as cursor:
            rows = await cursor.fetchall()
            import json

            documents = []
            for row in rows:
                doc = dict(row)
                doc["metadata"] = json.loads(doc.get("metadata", "{}"))
                documents.append(doc)

        return documents, total

    async def get_document(self, doc_id: str) -> Optional[dict]:
        """Get a single document by ID.

        Args:
            doc_id: Document ID.

        Returns:
            Document dict or None if not found.
        """
        return await self.db.get_document(doc_id)

    async def delete_document(self, doc_id: str) -> bool:
        """Delete a document by ID.

        Also removes the document from the FTS index.

        Args:
            doc_id: Document ID to delete.

        Returns:
            True if the document was deleted, False if not found.
        """
        doc = await self.db.get_document(doc_id)
        if doc is None:
            return False

        # Remove from FTS index
        await self.db._conn.execute(
            "DELETE FROM documents_fts WHERE id = ?", (doc_id,)
        )
        # Remove the document itself
        await self.db.delete_document(doc_id)
        return True

    async def search_documents(self, query: str, limit: int = 10) -> list[dict]:
        """Search documents using full-text search.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            List of matching document dicts with rank.
        """
        return await self.db.search_documents(query, limit)

    async def get_document_count_by_status(self, status: str) -> int:
        """Count documents with a specific status.

        Args:
            status: Status to count.

        Returns:
            Number of documents with the given status.
        """
        async with self.db._conn.execute(
            "SELECT COUNT(*) FROM documents WHERE status = ?", (status,)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_total_document_count(self) -> int:
        """Get total number of documents.

        Returns:
            Total document count.
        """
        async with self.db._conn.execute(
            "SELECT COUNT(*) FROM documents"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_wiki_count(self) -> int:
        """Count documents of type 'wiki' or get total concepts.

        Returns:
            Number of wiki entries.
        """
        async with self.db._conn.execute(
            "SELECT COUNT(*) FROM concepts"
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0
