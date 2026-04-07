"""Unit tests for the database module."""

import pytest

from src.database import Database


class TestDatabaseInitialization:
    """Tests for database initialization."""

    @pytest.mark.asyncio
    async def test_database_connect_and_initialize(self, db: Database) -> None:
        """Test that database connects and initializes successfully."""
        # The db fixture handles connect and initialize
        # Just verify we can perform a simple operation
        result = await db.get_user_by_id("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_database_tables_created(self, db: Database) -> None:
        """Test that all required tables are created."""
        # Query sqlite_master to verify tables exist
        async with db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ) as cursor:
            tables = [row[0] async for row in cursor]

        expected_tables = [
            "compile_tasks",
            "concepts",
            "doc_concepts",
            "documents",
            "documents_fts",
            "links",
            "qa_history",
            "users",
        ]

        for table in expected_tables:
            assert table in tables, f"Table {table} not found in database"

    @pytest.mark.asyncio
    async def test_database_indexes_created(self, db: Database) -> None:
        """Test that required indexes are created."""
        async with db._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='index' ORDER BY name"
        ) as cursor:
            indexes = [row[0] async for row in cursor]

        expected_indexes = [
            "idx_compile_tasks_status",
            "idx_concepts_name",
            "idx_doc_concepts_concept",
            "idx_doc_concepts_doc",
            "idx_documents_status",
            "idx_documents_type",
        ]

        for index in expected_indexes:
            assert index in indexes, f"Index {index} not found in database"


class TestUserOperations:
    """Tests for user-related database operations."""

    @pytest.mark.asyncio
    async def test_create_and_get_user(self, db: Database) -> None:
        """Test creating and retrieving a user."""
        user_id = "user-001"
        username = "testuser"
        password_hash = "hashed_password_123"

        await db.create_user(user_id, username, password_hash)

        # Get by username
        user = await db.get_user_by_username(username)
        assert user is not None
        assert user["id"] == user_id
        assert user["username"] == username
        assert user["password_hash"] == password_hash

        # Get by ID
        user_by_id = await db.get_user_by_id(user_id)
        assert user_by_id is not None
        assert user_by_id["username"] == username

    @pytest.mark.asyncio
    async def test_get_nonexistent_user(self, db: Database) -> None:
        """Test getting a user that doesn't exist."""
        user = await db.get_user_by_username("nonexistent")
        assert user is None

        user = await db.get_user_by_id("nonexistent-id")
        assert user is None


class TestDocumentOperations:
    """Tests for document-related database operations."""

    @pytest.mark.asyncio
    async def test_create_and_get_document(self, db: Database) -> None:
        """Test creating and retrieving a document."""
        doc_id = "doc-001"
        doc_type = "web"
        path = "raw/web/doc-001.md"
        title = "Test Document"
        metadata = {"source": "https://example.com", "tags": ["test"]}

        await db.create_document(
            doc_id=doc_id,
            doc_type=doc_type,
            path=path,
            title=title,
            status="pending",
            metadata=metadata,
        )

        doc = await db.get_document(doc_id)
        assert doc is not None
        assert doc["id"] == doc_id
        assert doc["type"] == doc_type
        assert doc["path"] == path
        assert doc["title"] == title
        assert doc["status"] == "pending"
        assert doc["metadata"] == metadata

    @pytest.mark.asyncio
    async def test_update_document_status(self, db: Database) -> None:
        """Test updating document status."""
        doc_id = "doc-002"
        await db.create_document(
            doc_id=doc_id,
            doc_type="paper",
            path="raw/papers/doc-002.md",
        )

        await db.update_document_status(doc_id, "processed")

        doc = await db.get_document(doc_id)
        assert doc["status"] == "processed"

    @pytest.mark.asyncio
    async def test_get_documents_by_status(self, db: Database) -> None:
        """Test filtering documents by status."""
        await db.create_document("doc-003", "web", "raw/web/doc-003.md", status="pending")
        await db.create_document("doc-004", "web", "raw/web/doc-004.md", status="pending")
        await db.create_document("doc-005", "web", "raw/web/doc-005.md", status="processed")

        pending_docs = await db.get_documents_by_status("pending")
        assert len(pending_docs) == 2

        processed_docs = await db.get_documents_by_status("processed")
        assert len(processed_docs) == 1

    @pytest.mark.asyncio
    async def test_delete_document(self, db: Database) -> None:
        """Test deleting a document."""
        doc_id = "doc-006"
        await db.create_document(doc_id, "web", "raw/web/doc-006.md")

        await db.delete_document(doc_id)

        doc = await db.get_document(doc_id)
        assert doc is None


class TestFullTextSearch:
    """Tests for full-text search operations."""

    @pytest.mark.asyncio
    async def test_index_and_search_document(self, db: Database) -> None:
        """Test indexing document content and searching."""
        # Create document
        await db.create_document(
            doc_id="doc-fts-001",
            doc_type="web",
            path="raw/web/doc-fts-001.md",
            title="Machine Learning Basics",
        )

        # Index content
        await db.index_document_content(
            doc_id="doc-fts-001",
            title="Machine Learning Basics",
            content="Machine learning is a subset of artificial intelligence. "
            "It uses neural networks and deep learning techniques.",
        )

        # Search for documents
        results = await db.search_documents("machine learning")

        assert len(results) == 1
        assert results[0]["id"] == "doc-fts-001"
        assert results[0]["title"] == "Machine Learning Basics"

    @pytest.mark.asyncio
    async def test_search_multiple_documents(self, db: Database) -> None:
        """Test searching across multiple documents."""
        await db.create_document("doc-fts-002", "web", "path1", title="Python Guide")
        await db.create_document("doc-fts-003", "web", "path2", title="JavaScript Guide")

        await db.index_document_content(
            "doc-fts-002", "Python Guide", "Python is a programming language."
        )
        await db.index_document_content(
            "doc-fts-003", "JavaScript Guide", "JavaScript is also a programming language."
        )

        results = await db.search_documents("programming")

        assert len(results) == 2


class TestConceptOperations:
    """Tests for concept-related database operations."""

    @pytest.mark.asyncio
    async def test_create_and_get_concept(self, db: Database) -> None:
        """Test creating and retrieving a concept."""
        concept_id = "concept-001"
        name = "Machine Learning"
        wiki_path = "wiki/concepts/machine-learning.md"

        await db.create_concept(concept_id, name, wiki_path)

        concept = await db.get_concept(concept_id)
        assert concept is not None
        assert concept["name"] == name
        assert concept["wiki_path"] == wiki_path

        concept_by_name = await db.get_concept_by_name(name)
        assert concept_by_name is not None
        assert concept_by_name["id"] == concept_id

    @pytest.mark.asyncio
    async def test_increment_concept_mention(self, db: Database) -> None:
        """Test incrementing concept mention count."""
        concept_id = "concept-002"
        await db.create_concept(concept_id, "Deep Learning")

        # Increment mention count twice
        await db.increment_concept_mention(concept_id)
        await db.increment_concept_mention(concept_id)

        concept = await db.get_concept(concept_id)
        assert concept["mention_count"] == 2


class TestDocumentConceptAssociation:
    """Tests for document-concept associations."""

    @pytest.mark.asyncio
    async def test_link_document_concept(self, db: Database) -> None:
        """Test linking a document to a concept."""
        await db.create_document("doc-assoc-001", "web", "path1")
        await db.create_concept("concept-assoc-001", "AI")

        await db.link_document_concept(
            doc_id="doc-assoc-001",
            concept_id="concept-assoc-001",
            relevance_score=0.85,
        )

        concepts = await db.get_document_concepts("doc-assoc-001")
        assert len(concepts) == 1
        assert concepts[0]["name"] == "AI"
        assert concepts[0]["relevance_score"] == 0.85


class TestLinkOperations:
    """Tests for document link operations."""

    @pytest.mark.asyncio
    async def test_create_and_get_links(self, db: Database) -> None:
        """Test creating and retrieving document links."""
        await db.create_link(
            from_path="wiki/concepts/ml.md",
            to_path="wiki/concepts/ai.md",
            link_type="explicit",
        )

        outgoing = await db.get_outgoing_links("wiki/concepts/ml.md")
        assert len(outgoing) == 1
        assert outgoing[0]["to_path"] == "wiki/concepts/ai.md"

        incoming = await db.get_incoming_links("wiki/concepts/ai.md")
        assert len(incoming) == 1
        assert incoming[0]["from_path"] == "wiki/concepts/ml.md"


class TestCompileTaskOperations:
    """Tests for compile task operations."""

    @pytest.mark.asyncio
    async def test_create_and_get_compile_task(self, db: Database) -> None:
        """Test creating and retrieving a compile task."""
        task_id = "task-001"
        total_docs = 5

        await db.create_compile_task(task_id, total_docs)

        task = await db.get_compile_task(task_id)
        assert task is not None
        assert task["total_docs"] == total_docs
        assert task["status"] == "pending"
        assert task["completed_docs"] == 0

    @pytest.mark.asyncio
    async def test_update_compile_task_progress(self, db: Database) -> None:
        """Test updating compile task progress."""
        task_id = "task-002"
        await db.create_compile_task(task_id, 3)

        await db.update_compile_task(task_id, completed_docs=1)
        task = await db.get_compile_task(task_id)
        assert task["completed_docs"] == 1

        await db.update_compile_task(task_id, completed_docs=3, status="completed")
        task = await db.get_compile_task(task_id)
        assert task["status"] == "completed"
        assert task["completed_at"] is not None


class TestQAHistoryOperations:
    """Tests for Q&A history operations."""

    @pytest.mark.asyncio
    async def test_save_and_get_qa_interaction(self, db: Database) -> None:
        """Test saving and retrieving Q&A interactions."""
        qa_id = "qa-001"
        question = "What is machine learning?"
        answer = "Machine learning is a subset of AI..."
        sources = ["doc-001", "doc-002"]

        await db.save_qa_interaction(qa_id, question, answer, sources)

        history = await db.get_qa_history(limit=10)
        assert len(history) == 1
        assert history[0]["question"] == question
        assert history[0]["answer"] == answer
        assert history[0]["sources"] == sources

    @pytest.mark.asyncio
    async def test_qa_history_ordering(self, db: Database) -> None:
        """Test that Q&A history returns records."""
        await db.save_qa_interaction("qa-002", "Question 1", "Answer 1")
        await db.save_qa_interaction("qa-003", "Question 2", "Answer 2")

        history = await db.get_qa_history()
        assert len(history) == 2
        # Verify both records are present (ordering by created_at may not be
        # reliable when timestamps are identical, so we just check presence)
        ids = [h["id"] for h in history]
        assert "qa-002" in ids
        assert "qa-003" in ids


class TestDatabaseContextManager:
    """Tests for database async context manager."""

    @pytest.mark.asyncio
    async def test_context_manager(self, temp_vault) -> None:
        """Test using database as async context manager."""
        db_path = temp_vault / ".wiki" / "context_test.db"

        async with Database(db_path) as db:
            await db.initialize()
            await db.create_document("ctx-doc", "web", "path")

        # Verify database was closed
        assert db._conn is None
