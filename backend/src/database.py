from __future__ import annotations
"""Database module for LLM Knowledge Base.

This module provides async SQLite database operations for managing
documents, concepts, users, and full-text search capabilities.
"""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import aiosqlite


class Database:
    """Async SQLite database manager for the knowledge base.

    Handles all data persistence including documents, concepts, users,
    and full-text search using FTS5.
    """

    def __init__(self, db_path: str | Path):
        """Initialize database with the given path.

        Args:
            db_path: Path to the SQLite database file.
        """
        self.db_path = Path(db_path)
        self._conn: Optional[aiosqlite.Connection] = None

    async def connect(self) -> None:
        """Establish database connection."""
        if self._conn is None:
            self._conn = await aiosqlite.connect(self.db_path)
            # Enable foreign keys
            await self._conn.execute("PRAGMA foreign_keys = ON")
            # Return rows as sqlite3.Row for dict-like access
            self._conn.row_factory = sqlite3.Row

    async def close(self) -> None:
        """Close database connection."""
        if self._conn:
            await self._conn.close()
            self._conn = None

    async def initialize(self) -> None:
        """Create all required tables if they don't exist."""
        if self._conn is None:
            await self.connect()

        await self._create_tables()
        await self._create_indexes()

    async def _create_tables(self) -> None:
        """Create all database tables."""
        # Users table
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Documents table
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                path TEXT NOT NULL,
                title TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT DEFAULT '{}'
            );
        """)

        # Full-text search virtual table for documents
        await self._conn.executescript("""
            CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                id,
                title,
                content,
                tokenize='porter unicode61'
            );
        """)

        # Concepts table
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS concepts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                wiki_path TEXT,
                mention_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Document-Concept associations
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS doc_concepts (
                doc_id TEXT NOT NULL,
                concept_id TEXT NOT NULL,
                relevance_score REAL DEFAULT 0.0,
                PRIMARY KEY (doc_id, concept_id),
                FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE,
                FOREIGN KEY (concept_id) REFERENCES concepts(id) ON DELETE CASCADE
            );
        """)

        # Links between documents
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS links (
                from_path TEXT NOT NULL,
                to_path TEXT NOT NULL,
                link_type TEXT NOT NULL DEFAULT 'explicit',
                confidence REAL DEFAULT 1.0,
                PRIMARY KEY (from_path, to_path, link_type)
            );
        """)

        # Compile tasks for tracking compilation jobs
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS compile_tasks (
                id TEXT PRIMARY KEY,
                status TEXT DEFAULT 'pending',
                total_docs INTEGER DEFAULT 0,
                completed_docs INTEGER DEFAULT 0,
                failed_docs INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                result TEXT
            );
        """)

        # Q&A history
        await self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS qa_history (
                id TEXT PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                sources TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        await self._conn.commit()

    async def _create_indexes(self) -> None:
        """Create indexes for better query performance."""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status)",
            "CREATE INDEX IF NOT EXISTS idx_documents_type ON documents(type)",
            "CREATE INDEX IF NOT EXISTS idx_concepts_name ON concepts(name)",
            "CREATE INDEX IF NOT EXISTS idx_doc_concepts_doc ON doc_concepts(doc_id)",
            "CREATE INDEX IF NOT EXISTS idx_doc_concepts_concept ON doc_concepts(concept_id)",
            "CREATE INDEX IF NOT EXISTS idx_compile_tasks_status ON compile_tasks(status)",
        ]

        for index_sql in indexes:
            await self._conn.execute(index_sql)

        await self._conn.commit()

    # --- User Operations ---

    async def create_user(
        self, user_id: str, username: str, password_hash: str
    ) -> None:
        """Create a new user.

        Args:
            user_id: Unique user identifier.
            username: Unique username.
            password_hash: Hashed password.
        """
        await self._conn.execute(
            "INSERT INTO users (id, username, password_hash) VALUES (?, ?, ?)",
            (user_id, username, password_hash),
        )
        await self._conn.commit()

    async def get_user_by_username(self, username: str) -> Optional[dict]:
        """Get user by username.

        Args:
            username: Username to look up.

        Returns:
            User dict or None if not found.
        """
        async with self._conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """Get user by ID.

        Args:
            user_id: User ID to look up.

        Returns:
            User dict or None if not found.
        """
        async with self._conn.execute(
            "SELECT * FROM users WHERE id = ?", (user_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def count_users(self) -> int:
        """Count total number of users.

        Returns:
            Number of users in the database.
        """
        async with self._conn.execute("SELECT COUNT(*) FROM users") as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

    # --- Document Operations ---

    async def create_document(
        self,
        doc_id: str,
        doc_type: str,
        path: str,
        title: Optional[str] = None,
        status: str = "pending",
        metadata: Optional[dict] = None,
    ) -> None:
        """Create a new document.

        Args:
            doc_id: Unique document identifier.
            doc_type: Type of document (web, paper, video, code).
            path: File path in the vault.
            title: Document title.
            status: Processing status (pending/processed).
            metadata: Additional metadata as dict.
        """
        metadata_json = json.dumps(metadata or {})
        await self._conn.execute(
            """INSERT INTO documents (id, type, path, title, status, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (doc_id, doc_type, path, title, status, metadata_json),
        )
        await self._conn.commit()

    async def get_document(self, doc_id: str) -> Optional[dict]:
        """Get document by ID.

        Args:
            doc_id: Document ID to look up.

        Returns:
            Document dict with metadata parsed, or None if not found.
        """
        async with self._conn.execute(
            "SELECT * FROM documents WHERE id = ?", (doc_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                doc = dict(row)
                doc["metadata"] = json.loads(doc.get("metadata", "{}"))
                return doc
            return None

    async def get_documents_by_status(self, status: str) -> list[dict]:
        """Get all documents with a specific status.

        Args:
            status: Status to filter by.

        Returns:
            List of document dicts.
        """
        async with self._conn.execute(
            "SELECT * FROM documents WHERE status = ?", (status,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def update_document_status(
        self, doc_id: str, status: str, metadata: Optional[dict] = None
    ) -> None:
        """Update document status and optionally metadata.

        Args:
            doc_id: Document ID to update.
            status: New status value.
            metadata: Optional updated metadata.
        """
        if metadata is not None:
            metadata_json = json.dumps(metadata)
            await self._conn.execute(
                """UPDATE documents
                   SET status = ?, updated_at = ?, metadata = ?
                   WHERE id = ?""",
                (status, datetime.now(timezone.utc).isoformat(), metadata_json, doc_id),
            )
        else:
            await self._conn.execute(
                """UPDATE documents
                   SET status = ?, updated_at = ?
                   WHERE id = ?""",
                (status, datetime.now(timezone.utc).isoformat(), doc_id),
            )
        await self._conn.commit()

    async def delete_document(self, doc_id: str) -> None:
        """Delete a document by ID.

        Args:
            doc_id: Document ID to delete.
        """
        await self._conn.execute(
            "DELETE FROM documents WHERE id = ?", (doc_id,)
        )
        await self._conn.commit()

    # --- Full-Text Search Operations ---

    async def index_document_content(
        self, doc_id: str, title: str, content: str
    ) -> None:
        """Index document content for full-text search.

        Args:
            doc_id: Document ID.
            title: Document title.
            content: Document content to index.
        """
        # First delete any existing entry
        await self._conn.execute(
            "DELETE FROM documents_fts WHERE id = ?", (doc_id,)
        )
        # Insert new entry
        await self._conn.execute(
            "INSERT INTO documents_fts (id, title, content) VALUES (?, ?, ?)",
            (doc_id, title, content),
        )
        await self._conn.commit()

    async def search_documents(self, query: str, limit: int = 10) -> list[dict]:
        """Search documents using full-text search.

        Args:
            query: Search query string.
            limit: Maximum number of results.

        Returns:
            List of matching document dicts with rank.
        """
        async with self._conn.execute(
            """SELECT d.*, fts.rank
               FROM documents_fts fts
               JOIN documents d ON fts.id = d.id
               WHERE documents_fts MATCH ?
               ORDER BY fts.rank
               LIMIT ?""",
            (query, limit),
        ) as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                doc = dict(row)
                doc["metadata"] = json.loads(doc.get("metadata", "{}"))
                results.append(doc)
            return results

    # --- Concept Operations ---

    async def create_concept(
        self,
        concept_id: str,
        name: str,
        wiki_path: Optional[str] = None,
    ) -> None:
        """Create a new concept.

        Args:
            concept_id: Unique concept identifier.
            name: Concept name.
            wiki_path: Path to the wiki page for this concept.
        """
        await self._conn.execute(
            "INSERT INTO concepts (id, name, wiki_path) VALUES (?, ?, ?)",
            (concept_id, name, wiki_path),
        )
        await self._conn.commit()

    async def get_concept(self, concept_id: str) -> Optional[dict]:
        """Get concept by ID.

        Args:
            concept_id: Concept ID to look up.

        Returns:
            Concept dict or None if not found.
        """
        async with self._conn.execute(
            "SELECT * FROM concepts WHERE id = ?", (concept_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_concept_by_name(self, name: str) -> Optional[dict]:
        """Get concept by name.

        Args:
            name: Concept name to look up.

        Returns:
            Concept dict or None if not found.
        """
        async with self._conn.execute(
            "SELECT * FROM concepts WHERE name = ?", (name,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def increment_concept_mention(self, concept_id: str) -> None:
        """Increment the mention count for a concept.

        Args:
            concept_id: Concept ID to update.
        """
        await self._conn.execute(
            """UPDATE concepts
               SET mention_count = mention_count + 1
               WHERE id = ?""",
            (concept_id,),
        )
        await self._conn.commit()

    # --- Document-Concept Association Operations ---

    async def link_document_concept(
        self, doc_id: str, concept_id: str, relevance_score: float = 0.0
    ) -> None:
        """Link a document to a concept.

        Args:
            doc_id: Document ID.
            concept_id: Concept ID.
            relevance_score: Relevance score for the association.
        """
        await self._conn.execute(
            """INSERT OR REPLACE INTO doc_concepts (doc_id, concept_id, relevance_score)
               VALUES (?, ?, ?)""",
            (doc_id, concept_id, relevance_score),
        )
        await self._conn.commit()

    async def get_document_concepts(self, doc_id: str) -> list[dict]:
        """Get all concepts linked to a document.

        Args:
            doc_id: Document ID.

        Returns:
            List of concept dicts with relevance scores.
        """
        async with self._conn.execute(
            """SELECT c.*, dc.relevance_score
               FROM doc_concepts dc
               JOIN concepts c ON dc.concept_id = c.id
               WHERE dc.doc_id = ?
               ORDER BY dc.relevance_score DESC""",
            (doc_id,),
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # --- Link Operations ---

    async def create_link(
        self,
        from_path: str,
        to_path: str,
        link_type: str = "explicit",
        confidence: float = 1.0,
    ) -> None:
        """Create a link between documents.

        Args:
            from_path: Source document path.
            to_path: Target document path.
            link_type: Type of link (explicit/inferred).
            confidence: Confidence score for inferred links.
        """
        await self._conn.execute(
            """INSERT OR REPLACE INTO links (from_path, to_path, link_type, confidence)
               VALUES (?, ?, ?, ?)""",
            (from_path, to_path, link_type, confidence),
        )
        await self._conn.commit()

    async def get_outgoing_links(self, from_path: str) -> list[dict]:
        """Get all outgoing links from a document.

        Args:
            from_path: Source document path.

        Returns:
            List of link dicts.
        """
        async with self._conn.execute(
            "SELECT * FROM links WHERE from_path = ?", (from_path,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    async def get_incoming_links(self, to_path: str) -> list[dict]:
        """Get all incoming links to a document.

        Args:
            to_path: Target document path.

        Returns:
            List of link dicts.
        """
        async with self._conn.execute(
            "SELECT * FROM links WHERE to_path = ?", (to_path,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

    # --- Compile Task Operations ---

    async def create_compile_task(
        self, task_id: str, total_docs: int = 0
    ) -> None:
        """Create a new compile task.

        Args:
            task_id: Unique task identifier.
            total_docs: Total number of documents to compile.
        """
        await self._conn.execute(
            """INSERT INTO compile_tasks (id, total_docs)
               VALUES (?, ?)""",
            (task_id, total_docs),
        )
        await self._conn.commit()

    async def get_compile_task(self, task_id: str) -> Optional[dict]:
        """Get compile task by ID.

        Args:
            task_id: Task ID to look up.

        Returns:
            Task dict or None if not found.
        """
        async with self._conn.execute(
            "SELECT * FROM compile_tasks WHERE id = ?", (task_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_compile_task(
        self,
        task_id: str,
        status: Optional[str] = None,
        completed_docs: Optional[int] = None,
        failed_docs: Optional[int] = None,
        result: Optional[str] = None,
    ) -> None:
        """Update compile task progress.

        Args:
            task_id: Task ID to update.
            status: New status (optional).
            completed_docs: Number of completed documents (optional).
            failed_docs: Number of failed documents (optional).
            result: Result message (optional).
        """
        updates = []
        params = []

        if status is not None:
            updates.append("status = ?")
            params.append(status)
            if status in ("completed", "failed"):
                updates.append("completed_at = ?")
                params.append(datetime.now(timezone.utc).isoformat())

        if completed_docs is not None:
            updates.append("completed_docs = ?")
            params.append(completed_docs)

        if failed_docs is not None:
            updates.append("failed_docs = ?")
            params.append(failed_docs)

        if result is not None:
            updates.append("result = ?")
            params.append(result)

        if updates:
            params.append(task_id)
            await self._conn.execute(
                f"UPDATE compile_tasks SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            await self._conn.commit()

    # --- Q&A History Operations ---

    async def save_qa_interaction(
        self,
        qa_id: str,
        question: str,
        answer: str,
        sources: Optional[list[str]] = None,
    ) -> None:
        """Save a Q&A interaction.

        Args:
            qa_id: Unique interaction identifier.
            question: User's question.
            answer: Generated answer.
            sources: List of source document IDs.
        """
        sources_json = json.dumps(sources or [])
        await self._conn.execute(
            """INSERT INTO qa_history (id, question, answer, sources)
               VALUES (?, ?, ?, ?)""",
            (qa_id, question, answer, sources_json),
        )
        await self._conn.commit()

    async def get_qa_history(self, limit: int = 50) -> list[dict]:
        """Get recent Q&A history.

        Args:
            limit: Maximum number of entries to return.

        Returns:
            List of Q&A interaction dicts.
        """
        async with self._conn.execute(
            """SELECT * FROM qa_history
               ORDER BY created_at DESC
               LIMIT ?""",
            (limit,),
        ) as cursor:
            rows = await cursor.fetchall()
            results = []
            for row in rows:
                qa = dict(row)
                qa["sources"] = json.loads(qa.get("sources", "[]"))
                results.append(qa)
            return results

    async def __aenter__(self) -> "Database":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.close()
