"""Integration tests for compile module."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user, get_db
from src.auth.router import router as auth_router
from src.config import Settings, get_settings
from src.database import Database
from src.models.user import User
from src.routers.compile import router as compile_router


def create_test_app() -> FastAPI:
    """Create a test FastAPI application with compile router."""
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(compile_router, prefix="/api/v1")
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
async def sample_doc(db: Database, temp_vault: Path) -> dict:
    """Create a sample pending document in the database and vault."""
    doc_id = "test-doc-001"
    title = "Machine Learning Basics"
    raw_content = """---
title: Machine Learning Basics
type: web
source: https://example.com/ml-basics
---

# Machine Learning Basics

Machine learning is a subset of artificial intelligence.
It focuses on building systems that learn from data.
"""

    # Save raw file to vault
    raw_path = temp_vault / "raw" / "web" / f"{doc_id}.md"
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(raw_content, encoding="utf-8")

    # Create database record
    await db.create_document(
        doc_id=doc_id,
        doc_type="web",
        path=f"raw/web/{doc_id}.md",
        title=title,
        status="pending",
        metadata={"source_url": "https://example.com/ml-basics"},
    )

    return {"id": doc_id, "title": title, "path": f"raw/web/{doc_id}.md"}


@pytest.fixture
async def sample_docs(db: Database, temp_vault: Path) -> list[dict]:
    """Create multiple sample pending documents."""
    docs = []
    for i in range(5):
        doc_id = f"test-doc-{i:03d}"
        title = f"Test Article {i}"
        raw_content = f"# {title}\n\nThis is test content for article {i}."

        raw_path = temp_vault / "raw" / "web" / f"{doc_id}.md"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(raw_content, encoding="utf-8")

        await db.create_document(
            doc_id=doc_id,
            doc_type="web",
            path=f"raw/web/{doc_id}.md",
            title=title,
            status="pending",
            metadata={"source_url": f"https://example.com/article-{i}"},
        )

        docs.append({"id": doc_id, "title": title})

    return docs


MOCK_LLM_RESPONSE = """## Summary

Machine learning is a core area of [[Artificial Intelligence]].

## Overview

Machine learning enables systems to learn from data. Key concepts include:

- **Supervised Learning**: Learning from labeled data
- **Unsupervised Learning**: Finding patterns in unlabeled data
- [[Neural Networks]] are a popular approach

Machine learning is closely related to [[Deep Learning]] and [[Data Science]]."""


class TestCompileSingleDocument:
    """Tests for compiling a single document."""

    @patch("src.routers.compile.LLMClient")
    def test_compile_single_document_success(
        self,
        mock_llm_class: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_doc: dict,
        temp_vault: Path,
        db: Database,
    ) -> None:
        """Test successful compilation of a single document."""
        # Mock LLM client
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=MOCK_LLM_RESPONSE)
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/compile",
            json={
                "doc_ids": [sample_doc["id"]],
                "output_language": "中文",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["total"] == 1
        assert data["completed"] == 1
        assert data["failed"] == 0
        assert data["results"] is not None
        assert len(data["results"]) == 1
        result = data["results"][0]
        assert result["success"] is True
        assert result["doc_id"] == sample_doc["id"]
        assert result["wiki_path"] == f"wiki/sources/{sample_doc['id']}.md"

        # Verify wiki file was created
        wiki_path = temp_vault / "wiki" / "sources" / f"{sample_doc['id']}.md"
        assert wiki_path.exists()
        wiki_content = wiki_path.read_text()
        assert "[[Artificial Intelligence]]" in wiki_content
        assert "[[Neural Networks]]" in wiki_content

    @patch("src.routers.compile.LLMClient")
    def test_compile_document_not_found(
        self,
        mock_llm_class: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test compilation of a non-existent document."""
        mock_llm = AsyncMock()
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/compile",
            json={
                "doc_ids": ["nonexistent-doc"],
                "output_language": "中文",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed"] == 0
        assert data["failed"] == 1
        assert data["results"][0]["success"] is False
        assert "not found" in data["results"][0]["error"].lower()

    @patch("src.routers.compile.LLMClient")
    def test_compile_llm_failure(
        self,
        mock_llm_class: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_doc: dict,
        temp_vault: Path,
    ) -> None:
        """Test compilation when LLM call fails."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(side_effect=Exception("API rate limit"))
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/compile",
            json={
                "doc_ids": [sample_doc["id"]],
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["completed"] == 0
        assert data["failed"] == 1
        assert data["results"][0]["success"] is False
        assert "LLM generation failed" in data["results"][0]["error"]


class TestCompileBatchSync:
    """Tests for batch compilation in sync mode (<=5 docs)."""

    @patch("src.routers.compile.LLMClient")
    def test_batch_compile_sync_success(
        self,
        mock_llm_class: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_docs: list[dict],
        temp_vault: Path,
    ) -> None:
        """Test successful sync batch compilation with 5 documents."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=MOCK_LLM_RESPONSE)
        mock_llm_class.return_value = mock_llm

        doc_ids = [d["id"] for d in sample_docs]
        response = client.post(
            "/api/v1/compile",
            json={
                "doc_ids": doc_ids,
                "output_language": "中文",
            },
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["total"] == 5
        assert data["completed"] == 5
        assert data["failed"] == 0
        assert data["task_id"] is None  # sync mode, no task_id
        assert len(data["results"]) == 5

        # Verify all wiki files were created
        for doc in sample_docs:
            wiki_path = temp_vault / "wiki" / "sources" / f"{doc['id']}.md"
            assert wiki_path.exists()

    @patch("src.routers.compile.LLMClient")
    def test_batch_compile_single_doc_sync(
        self,
        mock_llm_class: MagicMock,
        client: TestClient,
        auth_headers: dict[str, str],
        sample_doc: dict,
    ) -> None:
        """Test that single doc compilation uses sync mode (no task_id)."""
        mock_llm = AsyncMock()
        mock_llm.generate = AsyncMock(return_value=MOCK_LLM_RESPONSE)
        mock_llm_class.return_value = mock_llm

        response = client.post(
            "/api/v1/compile",
            json={"doc_ids": [sample_doc["id"]]},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] is None
        assert data["status"] == "completed"
        assert data["results"] is not None


class TestCompileAuth:
    """Tests for authentication requirements."""

    def test_compile_unauthorized(self, client: TestClient) -> None:
        """Test that compilation requires authentication."""
        response = client.post(
            "/api/v1/compile",
            json={"doc_ids": ["some-doc-id"]},
        )
        assert response.status_code == 401

    def test_get_task_status_unauthorized(self, client: TestClient) -> None:
        """Test that getting task status requires authentication."""
        response = client.get("/api/v1/compile/tasks/some-task-id")
        assert response.status_code == 401

    def test_list_tasks_unauthorized(self, client: TestClient) -> None:
        """Test that listing tasks requires authentication."""
        response = client.get("/api/v1/compile/tasks")
        assert response.status_code == 401


class TestTaskStatus:
    """Tests for task status and listing endpoints."""

    def test_get_task_status_not_found(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test getting a non-existent task returns 404."""
        response = client.get(
            "/api/v1/compile/tasks/nonexistent-task",
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_list_tasks_empty(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test listing tasks when no tasks exist."""
        response = client.get(
            "/api/v1/compile/tasks",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["tasks"] == []

    def test_list_tasks_returns_existing(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        db: Database,
    ) -> None:
        """Test listing tasks returns existing tasks."""
        # Create a task directly in the database
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            db.create_compile_task("test-task-001", total_docs=3)
        )

        response = client.get(
            "/api/v1/compile/tasks",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["tasks"]) == 1
        assert data["tasks"][0]["id"] == "test-task-001"
        assert data["tasks"][0]["total_docs"] == 3

    def test_get_task_status_existing(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
        db: Database,
    ) -> None:
        """Test getting status of an existing task."""
        import asyncio
        asyncio.get_event_loop().run_until_complete(
            db.create_compile_task("test-task-002", total_docs=5)
        )
        asyncio.get_event_loop().run_until_complete(
            db.update_compile_task("test-task-002", completed_docs=3)
        )

        response = client.get(
            "/api/v1/compile/tasks/test-task-002",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "test-task-002"
        assert data["total_docs"] == 5
        assert data["completed_docs"] == 3


class TestCompileValidation:
    """Tests for request validation."""

    def test_compile_empty_doc_ids(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that empty doc_ids list returns validation error."""
        response = client.post(
            "/api/v1/compile",
            json={"doc_ids": []},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_compile_missing_doc_ids(
        self,
        client: TestClient,
        auth_headers: dict[str, str],
    ) -> None:
        """Test that missing doc_ids returns validation error."""
        response = client.post(
            "/api/v1/compile",
            json={"output_language": "中文"},
            headers=auth_headers,
        )
        assert response.status_code == 422
