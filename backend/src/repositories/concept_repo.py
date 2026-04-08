"""Concept repository for database operations."""

import uuid
from typing import Optional

from src.database import Database


class ConceptRepo:
    """Repository for concept-related database operations."""

    def __init__(self, db: Database) -> None:
        """Initialize the concept repository.

        Args:
            db: Database instance.
        """
        self.db = db

    async def create(
        self,
        name: str,
        wiki_path: Optional[str] = None,
    ) -> str:
        """Create a new concept.

        Args:
            name: Concept name.
            wiki_path: Optional path to wiki page.

        Returns:
            The created concept's ID.
        """
        concept_id = str(uuid.uuid4())
        await self.db.create_concept(
            concept_id=concept_id,
            name=name,
            wiki_path=wiki_path,
        )
        return concept_id

    async def get_by_id(self, concept_id: str) -> Optional[dict]:
        """Get a concept by ID.

        Args:
            concept_id: The concept ID.

        Returns:
            Concept dict or None.
        """
        return await self.db.get_concept(concept_id)

    async def get_by_name(self, name: str) -> Optional[dict]:
        """Get a concept by name.

        Args:
            name: The concept name.

        Returns:
            Concept dict or None.
        """
        return await self.db.get_concept_by_name(name)

    async def list_all(
        self,
        page: int = 1,
        limit: int = 50,
    ) -> tuple[list[dict], int]:
        """List all concepts with pagination.

        Args:
            page: Page number (1-indexed).
            limit: Items per page.

        Returns:
            Tuple of (concepts list, total count).
        """
        offset = (page - 1) * limit

        async with self.db._conn.execute(
            "SELECT COUNT(*) FROM concepts"
        ) as cursor:
            row = await cursor.fetchone()
            total = row[0] if row else 0

        async with self.db._conn.execute(
            """SELECT * FROM concepts
               ORDER BY mention_count DESC, created_at DESC
               LIMIT ? OFFSET ?""",
            (limit, offset),
        ) as cursor:
            rows = await cursor.fetchall()
            concepts = [dict(row) for row in rows]

        return concepts, total

    async def find_or_create(
        self,
        name: str,
        wiki_path: Optional[str] = None,
    ) -> str:
        """Find an existing concept by name or create a new one.

        Args:
            name: Concept name.
            wiki_path: Optional path to wiki page.

        Returns:
            The concept ID.
        """
        existing = await self.get_by_name(name)
        if existing:
            return existing["id"]

        return await self.create(name=name, wiki_path=wiki_path)

    async def link_to_document(
        self,
        doc_id: str,
        concept_id: str,
        relevance_score: float = 0.0,
    ) -> None:
        """Link a concept to a document.

        Args:
            doc_id: Document ID.
            concept_id: Concept ID.
            relevance_score: Relevance score.
        """
        await self.db.link_document_concept(
            doc_id=doc_id,
            concept_id=concept_id,
            relevance_score=relevance_score,
        )

    async def get_document_concepts(self, doc_id: str) -> list[dict]:
        """Get all concepts for a document.

        Args:
            doc_id: Document ID.

        Returns:
            List of concept dicts with relevance scores.
        """
        return await self.db.get_document_concepts(doc_id)

    async def delete(self, concept_id: str) -> bool:
        """Delete a concept.

        Args:
            concept_id: The concept ID to delete.

        Returns:
            True if deleted, False if not found.
        """
        cursor = await self.db._conn.execute(
            "DELETE FROM concepts WHERE id = ?",
            (concept_id,),
        )
        await self.db._conn.commit()
        return cursor.rowcount > 0
