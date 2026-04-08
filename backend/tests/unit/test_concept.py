"""Tests for the concept module."""

import pytest
import pytest_asyncio

from src.database import Database
from src.repositories.concept_repo import ConceptRepo
from src.models.concept import Concept, ConceptSummary, ConceptListResponse


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database for testing."""
    import asyncio

    async def _create():
        db = Database(tmp_path / "test.db")
        await db.connect()
        await db.initialize()
        return db

    return asyncio.get_event_loop().run_until_complete(_create())


@pytest.fixture
def temp_db_async(tmp_path):
    """Create a temporary async database."""
    return tmp_path


@pytest.mark.asyncio
async def test_concept_repo_create(temp_db_async, tmp_path):
    """Test creating a concept via repo."""
    db = Database(tmp_path / "test.db")
    await db.connect()
    await db.initialize()

    repo = ConceptRepo(db)
    concept_id = await repo.create(name="Python", wiki_path="wiki/concepts/python.md")
    assert concept_id is not None

    concept = await repo.get_by_id(concept_id)
    assert concept is not None
    assert concept["name"] == "Python"
    assert concept["wiki_path"] == "wiki/concepts/python.md"

    await db.close()


@pytest.mark.asyncio
async def test_concept_repo_get_by_name(temp_db_async, tmp_path):
    """Test getting a concept by name."""
    db = Database(tmp_path / "test.db")
    await db.connect()
    await db.initialize()

    repo = ConceptRepo(db)
    await repo.create(name="Machine Learning")

    concept = await repo.get_by_name("Machine Learning")
    assert concept is not None
    assert concept["name"] == "Machine Learning"

    await db.close()


@pytest.mark.asyncio
async def test_concept_repo_find_or_create(temp_db_async, tmp_path):
    """Test find_or_create returns existing or creates new."""
    db = Database(tmp_path / "test.db")
    await db.connect()
    await db.initialize()

    repo = ConceptRepo(db)

    # First call creates
    id1 = await repo.find_or_create(name="FastAPI")
    assert id1 is not None

    # Second call returns existing
    id2 = await repo.find_or_create(name="FastAPI")
    assert id1 == id2

    await db.close()


@pytest.mark.asyncio
async def test_concept_repo_list(temp_db_async, tmp_path):
    """Test listing concepts with pagination."""
    db = Database(tmp_path / "test.db")
    await db.connect()
    await db.initialize()

    repo = ConceptRepo(db)
    await repo.create(name="Python")
    await repo.create(name="Rust")
    await repo.create(name="Go")

    concepts, total = await repo.list_all(page=1, limit=2)
    assert total == 3
    assert len(concepts) == 2

    await db.close()


@pytest.mark.asyncio
async def test_concept_repo_link_to_document(temp_db_async, tmp_path):
    """Test linking a concept to a document."""
    db = Database(tmp_path / "test.db")
    await db.connect()
    await db.initialize()

    repo = ConceptRepo(db)
    concept_id = await repo.create(name="Docker")

    # Create a document first
    await db.create_document(
        doc_id="doc-1", doc_type="web", path="raw/web/doc.md",
        title="Test", status="pending"
    )

    await repo.link_to_document("doc-1", concept_id, relevance_score=0.9)

    concepts = await repo.get_document_concepts("doc-1")
    assert len(concepts) == 1
    assert concepts[0]["name"] == "Docker"

    await db.close()


@pytest.mark.asyncio
async def test_concept_repo_delete(temp_db_async, tmp_path):
    """Test deleting a concept."""
    db = Database(tmp_path / "test.db")
    await db.connect()
    await db.initialize()

    repo = ConceptRepo(db)
    concept_id = await repo.create(name="ToDelete")

    deleted = await repo.delete(concept_id)
    assert deleted is True

    concept = await repo.get_by_id(concept_id)
    assert concept is None

    await db.close()


def test_concept_models():
    """Test Pydantic models."""
    concept = Concept(
        id="test-id",
        name="Test Concept",
        wiki_path="wiki/test.md",
        mention_count=5,
        created_at="2024-01-01",
    )
    assert concept.id == "test-id"
    assert concept.name == "Test Concept"

    summary = ConceptSummary(
        id="test-id",
        name="Test",
        mention_count=1,
        created_at="2024-01-01",
    )
    assert summary.name == "Test"

    response = ConceptListResponse(
        total=1, page=1, limit=50, items=[summary]
    )
    assert response.total == 1
