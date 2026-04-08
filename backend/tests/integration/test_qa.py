"""Integration tests for QA service and router."""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.auth.dependencies import get_current_user, get_db
from src.auth.router import router as auth_router
from src.database import Database
from src.repositories.document_repo import DocumentRepo
from src.routers.qa import router as qa_router
from src.services.qa import QAResult, QAService


def create_test_app() -> FastAPI:
    """Create a test FastAPI application with QA router."""
    app = FastAPI()
    app.include_router(auth_router, prefix="/api/v1")
    app.include_router(qa_router, prefix="/api/v1")
    return app


@pytest.fixture
def app() -> FastAPI:
    """Create a test FastAPI application."""
    return create_test_app()


@pytest.fixture
def client(app: FastAPI, db: Database) -> TestClient:
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


class TestQAService:
    """Tests for QAService."""

    @pytest.fixture
    def doc_repo(self, db: Database) -> DocumentRepo:
        """Create a document repository."""
        return DocumentRepo(db)

    @pytest.fixture
    async def setup_documents(self, db: Database) -> None:
        """Set up test documents for searching."""
        await db.create_document(
            doc_id="doc-1",
            doc_type="web",
            path="raw/web/doc-1.md",
            title="Introduction to Machine Learning",
            status="processed",
            metadata={"source_url": "https://example.com/ml-intro"},
        )
        await db.create_document(
            doc_id="doc-2",
            doc_type="paper",
            path="raw/papers/doc-2.md",
            title="Deep Learning Fundamentals",
            status="processed",
            metadata={"source_url": "https://example.com/dl-fundamentals"},
        )
        # Index documents for FTS
        await db.index_document_content(
            doc_id="doc-1",
            title="Introduction to Machine Learning",
            content="Machine learning is a subset of artificial intelligence. "
            "It enables systems to learn from data.",
        )
        await db.index_document_content(
            doc_id="doc-2",
            title="Deep Learning Fundamentals",
            content="Deep learning uses neural networks with many layers. "
            "It is a powerful technique for AI.",
        )

    @pytest.mark.asyncio
    async def test_ask_success(
        self, doc_repo: DocumentRepo, setup_documents: None
    ) -> None:
        """Test successful question answering."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(
            return_value="Machine learning is a subset of artificial intelligence "
            "that enables systems to learn from data. [source:doc-1]"
        )

        qa_service = QAService(doc_repo=doc_repo, llm_client=mock_llm)
        result = await qa_service.ask(
            question="machine learning",
            top_k=5,
        )

        assert result.answer is not None
        assert "Machine learning" in result.answer
        assert len(result.sources) > 0
        assert result.sources[0]["id"] in ["doc-1", "doc-2"]

    @pytest.mark.asyncio
    async def test_ask_with_language(
        self, doc_repo: DocumentRepo, setup_documents: None
    ) -> None:
        """Test QA with custom output language."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(
            return_value="Machine learning is a subset of artificial intelligence."
        )

        qa_service = QAService(doc_repo=doc_repo, llm_client=mock_llm)
        result = await qa_service.ask(
            question="machine learning",
            top_k=5,
            output_language="English",
        )

        assert result.answer is not None

    @pytest.mark.asyncio
    async def test_stream_ask(
        self, doc_repo: DocumentRepo, setup_documents: None
    ) -> None:
        """Test streaming question answering."""
        async def mock_stream(*args, **kwargs):
            for chunk in ["Machine", " learning", " is", " AI."]:
                yield chunk

        mock_llm = MagicMock()
        mock_llm.stream = mock_stream

        qa_service = QAService(doc_repo=doc_repo, llm_client=mock_llm)
        chunks = []
        async for chunk in qa_service.stream_ask(
            question="machine learning",
            top_k=5,
        ):
            chunks.append(chunk)

        assert len(chunks) == 4
        assert "".join(chunks) == "Machine learning is AI."

    @pytest.mark.asyncio
    async def test_ask_no_results(self, doc_repo: DocumentRepo) -> None:
        """Test QA when no documents match the query."""
        mock_llm = MagicMock()
        mock_llm.generate = AsyncMock(
            return_value="I don't have any relevant information about that topic."
        )

        qa_service = QAService(doc_repo=doc_repo, llm_client=mock_llm)
        result = await qa_service.ask(
            question="quantum computing",
            top_k=5,
        )

        # Should return an answer even with no sources
        assert result.answer is not None
        assert result.sources == []


class TestQARouter:
    """Tests for QA router endpoints."""

    def test_ask_question_success(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Test successful ask question endpoint."""
        with patch("src.routers.qa.QAService") as MockQAService:
            # Setup mock service
            mock_service = MagicMock()
            mock_result = QAResult(
                answer="Machine learning is AI.",
                sources=[{"id": "doc-1", "title": "ML Guide", "relevance": 0.9}],
                related_concepts=["AI", "Neural Networks"],
            )
            mock_service.ask = AsyncMock(return_value=mock_result)
            MockQAService.return_value = mock_service

            response = client.post(
                "/api/v1/qa/ask",
                json={
                    "question": "What is machine learning?",
                    "stream": False,
                    "top_k": 5,
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            data = response.json()
            assert "answer" in data
            assert "sources" in data
            assert "related_concepts" in data

    def test_ask_question_with_stream(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Test ask question endpoint with streaming."""
        with patch("src.routers.qa.QAService") as MockQAService:
            # Setup mock streaming
            async def mock_stream(*args, **kwargs):
                for chunk in ["Hello", " World"]:
                    yield chunk

            mock_service = MagicMock()
            mock_service.stream_ask = mock_stream
            MockQAService.return_value = mock_service

            response = client.post(
                "/api/v1/qa/ask",
                json={
                    "question": "Hello?",
                    "stream": True,
                    "top_k": 5,
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            # Verify it returns streaming response (SSE)
            assert "text/event-stream" in response.headers.get("content-type", "")

    def test_ask_question_auth_required(self, client: TestClient) -> None:
        """Test that ask question endpoint requires authentication."""
        response = client.post(
            "/api/v1/qa/ask",
            json={
                "question": "What is machine learning?",
                "stream": False,
                "top_k": 5,
            },
        )

        assert response.status_code == 401

    def test_ask_question_validation(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Test request validation for ask question."""
        # Missing question
        response = client.post(
            "/api/v1/qa/ask",
            json={
                "stream": False,
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    def test_ask_question_default_params(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Test ask question with default parameters."""
        with patch("src.routers.qa.QAService") as MockQAService:
            mock_service = MagicMock()
            mock_result = QAResult(
                answer="Test answer",
                sources=[],
                related_concepts=[],
            )
            mock_service.ask = AsyncMock(return_value=mock_result)
            MockQAService.return_value = mock_service

            response = client.post(
                "/api/v1/qa/ask",
                json={
                    "question": "Test question?",
                },
                headers=auth_headers,
            )

            assert response.status_code == 200
            # Verify default values were used
            mock_service.ask.assert_called_once()
            call_args = mock_service.ask.call_args
            assert call_args[1].get("top_k", call_args[0][1] if len(call_args[0]) > 1 else 5) == 5


class TestQAResult:
    """Tests for QAResult dataclass."""

    def test_to_dict(self) -> None:
        """Test QAResult serialization."""
        result = QAResult(
            answer="Test answer",
            sources=[{"id": "doc-1", "title": "Test", "relevance": 0.9}],
            related_concepts=["AI", "ML"],
        )

        data = result.to_dict()
        assert data["answer"] == "Test answer"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["id"] == "doc-1"
        assert data["related_concepts"] == ["AI", "ML"]

    def test_to_dict_empty(self) -> None:
        """Test QAResult serialization with empty defaults."""
        result = QAResult(answer="Simple answer")

        data = result.to_dict()
        assert data["answer"] == "Simple answer"
        assert data["sources"] == []
        assert data["related_concepts"] == []
