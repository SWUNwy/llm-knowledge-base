"""Integration tests for ingest module."""

from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user, get_db
from src.auth.router import router as auth_router
from src.database import Database
from src.models.user import User
from src.routers.ingest import router as ingest_router
from src.parsers.base import ParseResult


def create_test_app() -> FastAPI:
    """Create a test FastAPI application with ingest router."""
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(ingest_router, prefix="/api/v1")
    return app


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI application."""
    return create_test_app()


@pytest.fixture
def client(app: FastAPI, db: Database, temp_vault: Path) -> TestClient:
    """Create a test client with database and config dependency overrides."""
    # Override get_db to use test database
    async def _get_db() -> Database:
        return db

    app.dependency_overrides[get_db] = _get_db

    # Override config to use temp vault
    from src.config import get_settings, Settings

    test_settings = Settings(
        vault_path=str(temp_vault),
        app_secret_key="test-secret-key-for-jwt-testing",
    )

    def _get_test_settings():
        return test_settings

    app.dependency_overrides[get_settings] = _get_test_settings

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_token(client: TestClient) -> str:
    """Create a user and return auth token."""
    # Setup account
    response = client.post(
        "/api/v1/auth/setup",
        json={"username": "testuser", "password": "testpass123"},
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Create authorization headers with valid token."""
    return {"Authorization": f"Bearer {auth_token}"}


class TestIngestURL:
    """Tests for POST /api/v1/ingest/url endpoint."""

    @patch("src.services.ingest.WebParser")
    def test_ingest_url_success(
        self,
        mock_web_parser: AsyncMock,
        client: TestClient,
        auth_headers: dict[str, str],
        temp_vault: Path,
    ) -> None:
        """Test successful URL import."""
        # Mock the WebParser
        mock_parser = AsyncMock()
        mock_parser.parse_url = AsyncMock(
            return_value=ParseResult(
                success=True,
                title="Test Article",
                content="This is the test content.",
                metadata={"source_url": "https://example.com/article"},
            )
        )
        mock_web_parser.return_value = mock_parser

        response = client.post(
            "/api/v1/ingest/url",
            json={
                "url": "https://example.com/article",
                "tags": ["test", "example"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "doc_id" in data
        assert data["title"] == "Test Article"
        assert data["path"].startswith("raw/web/")

    @patch("src.services.ingest.WebParser")
    def test_ingest_url_with_empty_tags(
        self,
        mock_web_parser: AsyncMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test URL import with empty tags."""
        mock_parser = AsyncMock()
        mock_parser.parse_url = AsyncMock(
            return_value=ParseResult(
                success=True,
                title="Test Article",
                content="Content here.",
            )
        )
        mock_web_parser.return_value = mock_parser

        response = client.post(
            "/api/v1/ingest/url",
            json={"url": "https://example.com/article"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        assert response.json()["success"] is True

    @patch("src.services.ingest.WebParser")
    def test_ingest_url_parse_failure(
        self,
        mock_web_parser: AsyncMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test URL import when parsing fails."""
        mock_parser = AsyncMock()
        mock_parser.parse_url = AsyncMock(
            return_value=ParseResult(
                success=False,
                error="Failed to fetch URL",
            )
        )
        mock_web_parser.return_value = mock_parser

        response = client.post(
            "/api/v1/ingest/url",
            json={"url": "https://example.com/404"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        assert "failed" in response.json()["detail"].lower()

    def test_ingest_url_missing_url(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test URL import with missing URL returns validation error."""
        response = client.post(
            "/api/v1/ingest/url",
            json={"tags": ["test"]},
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_ingest_url_unauthorized(self, client: TestClient) -> None:
        """Test URL import without authentication returns 401."""
        response = client.post(
            "/api/v1/ingest/url",
            json={"url": "https://example.com/article"},
        )

        assert response.status_code == 401


class TestIngestFile:
    """Tests for POST /api/v1/ingest/file endpoint."""

    def test_ingest_file_not_found(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test file import with non-existent file returns 404."""
        response = client.post(
            "/api/v1/ingest/file",
            json={
                "path": "/non/existent/file.pdf",
                "tags": ["test"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_ingest_file_html_success(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        temp_vault: Path,
    ) -> None:
        """Test successful HTML file import."""
        # Create a test HTML file
        test_file = temp_vault / "test_input.html"
        test_file.write_text("""
        <html>
            <head><title>Test HTML</title></head>
            <body><h1>Hello World</h1><p>Test content here.</p></body>
        </html>
        """)

        response = client.post(
            "/api/v1/ingest/file",
            json={
                "path": str(test_file),
                "tags": ["html", "test"],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "doc_id" in data
        assert data["path"].startswith("raw/web/")

    def test_ingest_file_unauthorized(self, client: TestClient) -> None:
        """Test file import without authentication returns 401."""
        response = client.post(
            "/api/v1/ingest/file",
            json={"path": "/some/file.pdf"},
        )

        assert response.status_code == 401

    def test_ingest_file_missing_path(
        self, client: TestClient, auth_headers: dict[str, str]
    ) -> None:
        """Test file import with missing path returns validation error."""
        response = client.post(
            "/api/v1/ingest/file",
            json={"tags": ["test"]},
            headers=auth_headers,
        )

        assert response.status_code == 422
