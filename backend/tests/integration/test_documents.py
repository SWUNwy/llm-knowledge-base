"""Integration tests for document and system routes."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user, get_db
from src.auth.router import router as auth_router
from src.database import Database
from src.routers.documents import router as document_router
from src.routers.system import router as system_router


def create_test_app() -> FastAPI:
    """Create a test FastAPI application with document and system routers."""
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(document_router, prefix="/api/v1")
    app.include_router(system_router, prefix="/api/v1")
    return app


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI application."""
    return create_test_app()


@pytest.fixture
def client(app: FastAPI, db: Database, temp_vault: Path) -> TestClient:
    """Create a test client with database dependency override."""
    async def _get_db() -> Database:
        return db

    app.dependency_overrides[get_db] = _get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_token(client: TestClient) -> str:
    """Create a user and return auth token."""
    response = client.post(
        "/api/v1/auth/setup",
        json={"username": "testuser", "password": "testpass123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Create authorization headers with valid token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
async def sample_documents(db: Database) -> list[dict]:
    """Create sample documents in the database for testing.

    Returns:
        List of created document dicts.
    """
    docs = [
        {
            "id": "doc-001",
            "doc_type": "web",
            "path": "raw/web/doc-001.md",
            "title": "Introduction to Python",
            "status": "processed",
            "metadata": {"tags": ["python", "programming"]},
        },
        {
            "id": "doc-002",
            "doc_type": "paper",
            "path": "raw/papers/doc-002.md",
            "title": "Attention Is All You Need",
            "status": "processed",
            "metadata": {"tags": ["transformers", "nlp"]},
        },
        {
            "id": "doc-003",
            "doc_type": "web",
            "path": "raw/web/doc-003.md",
            "title": "FastAPI Tutorial",
            "status": "pending",
            "metadata": {"tags": ["fastapi", "python"]},
        },
        {
            "id": "doc-004",
            "doc_type": "video",
            "path": "raw/videos/doc-004.md",
            "title": "Machine Learning Basics",
            "status": "pending",
            "metadata": {"tags": ["ml", "tutorial"]},
        },
    ]

    for doc in docs:
        await db.create_document(
            doc_id=doc["id"],
            doc_type=doc["doc_type"],
            path=doc["path"],
            title=doc["title"],
            status=doc["status"],
            metadata=doc["metadata"],
        )

    return docs


class TestListDocuments:
    """Tests for GET /api/v1/documents endpoint."""

    @pytest.mark.asyncio
    async def test_list_documents_empty(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test listing documents when database is empty."""
        response = client.get("/api/v1/documents", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []
        assert data["page"] == 1

    @pytest.mark.asyncio
    async def test_list_documents_with_data(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_documents: list[dict],
    ) -> None:
        """Test listing documents returns all documents."""
        response = client.get("/api/v1/documents", headers=auth_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["items"]) == 4

    @pytest.mark.asyncio
    async def test_list_documents_filter_by_type(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_documents: list[dict],
    ) -> None:
        """Test filtering documents by type."""
        response = client.get(
            "/api/v1/documents?type=web", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["type"] == "web" for item in data["items"])

    @pytest.mark.asyncio
    async def test_list_documents_filter_by_status(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_documents: list[dict],
    ) -> None:
        """Test filtering documents by status."""
        response = client.get(
            "/api/v1/documents?status=pending", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert all(item["status"] == "pending" for item in data["items"])

    @pytest.mark.asyncio
    async def test_list_documents_pagination(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_documents: list[dict],
    ) -> None:
        """Test pagination of document listing."""
        response = client.get(
            "/api/v1/documents?page=1&limit=2", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["items"]) == 2
        assert data["page"] == 1
        assert data["limit"] == 2

    @pytest.mark.asyncio
    async def test_list_documents_second_page(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_documents: list[dict],
    ) -> None:
        """Test second page of paginated results."""
        response = client.get(
            "/api/v1/documents?page=2&limit=2", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 4
        assert len(data["items"]) == 2
        assert data["page"] == 2

    def test_list_documents_unauthorized(self, client: TestClient) -> None:
        """Test listing documents without auth returns 401."""
        response = client.get("/api/v1/documents")

        assert response.status_code == 401


class TestGetDocument:
    """Tests for GET /api/v1/documents/{doc_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_document_found(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_documents: list[dict],
    ) -> None:
        """Test getting an existing document by ID."""
        response = client.get(
            "/api/v1/documents/doc-001", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "doc-001"
        assert data["title"] == "Introduction to Python"
        assert data["type"] == "web"
        assert data["status"] == "processed"
        assert data["path"] == "raw/web/doc-001.md"
        assert data["metadata"]["tags"] == ["python", "programming"]

    @pytest.mark.asyncio
    async def test_get_document_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test getting a non-existent document returns 404."""
        response = client.get(
            "/api/v1/documents/nonexistent", headers=auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_document_unauthorized(self, client: TestClient) -> None:
        """Test getting a document without auth returns 401."""
        response = client.get("/api/v1/documents/doc-001")

        assert response.status_code == 401


class TestDeleteDocument:
    """Tests for DELETE /api/v1/documents/{doc_id} endpoint."""

    @pytest.mark.asyncio
    async def test_delete_document_success(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_documents: list[dict],
    ) -> None:
        """Test deleting an existing document."""
        response = client.delete(
            "/api/v1/documents/doc-001", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "deleted" in data["message"].lower()

        # Verify it's actually gone
        response = client.get(
            "/api/v1/documents/doc-001", headers=auth_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_document_not_found(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test deleting a non-existent document returns 404."""
        response = client.delete(
            "/api/v1/documents/nonexistent", headers=auth_headers
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_document_unauthorized(self, client: TestClient) -> None:
        """Test deleting a document without auth returns 401."""
        response = client.delete("/api/v1/documents/doc-001")

        assert response.status_code == 401


class TestSearchDocuments:
    """Tests for GET /api/v1/documents/search endpoint."""

    @pytest.mark.asyncio
    async def test_search_documents_with_results(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        db: Database,
    ) -> None:
        """Test searching documents returns matching results."""
        # Create a document and index its content
        await db.create_document(
            doc_id="search-doc-1",
            doc_type="web",
            path="raw/web/search-doc-1.md",
            title="Python Async Programming",
            status="processed",
        )
        await db.index_document_content(
            doc_id="search-doc-1",
            title="Python Async Programming",
            content="Async programming in Python uses async and await keywords",
        )

        response = client.get(
            "/api/v1/documents/search?q=python+async", headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(
            item["id"] == "search-doc-1" for item in data["items"]
        )

    @pytest.mark.asyncio
    async def test_search_documents_no_results(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_documents: list[dict],
    ) -> None:
        """Test searching with a non-matching query returns empty results."""
        response = client.get(
            "/api/v1/documents/search?q=zzzznonexistentzzzz",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["items"] == []

    def test_search_documents_unauthorized(self, client: TestClient) -> None:
        """Test searching documents without auth returns 401."""
        response = client.get("/api/v1/documents/search?q=test")

        assert response.status_code == 401

    def test_search_documents_missing_query(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test searching without query parameter returns validation error."""
        response = client.get(
            "/api/v1/documents/search", headers=auth_headers
        )

        assert response.status_code == 422


class TestSystemStatus:
    """Tests for GET /api/v1/system/status endpoint."""

    def test_system_status_empty(self, client: TestClient) -> None:
        """Test system status with empty database."""
        response = client.get("/api/v1/system/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["total_documents"] == 0
        assert data["pending_documents"] == 0
        assert data["processed_documents"] == 0
        assert data["wiki_count"] == 0

    @pytest.mark.asyncio
    async def test_system_status_with_data(
        self,
        client: TestClient,
        sample_documents: list[dict],
    ) -> None:
        """Test system status returns correct counts."""
        response = client.get("/api/v1/system/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["total_documents"] == 4
        assert data["pending_documents"] == 2
        assert data["processed_documents"] == 2

    def test_system_status_no_auth_required(self, client: TestClient) -> None:
        """Test system status endpoint does not require authentication."""
        response = client.get("/api/v1/system/status")

        assert response.status_code == 200
