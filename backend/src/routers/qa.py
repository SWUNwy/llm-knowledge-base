from __future__ import annotations
"""QA router for question-answering endpoints."""

import json
import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.auth.dependencies import get_current_user, get_db
from src.database import Database
from src.errors import AppError, ErrorCode
from src.llm.client import LLMClient
from src.models.user import User
from src.repositories.document_repo import DocumentRepo
from src.services.qa import QAService

logger = logging.getLogger(__name__)

# Request models


class QARequest(BaseModel):
    """Request model for asking a question."""

    question: str = Field(
        ...,
        min_length=1,
        description="The question to ask",
    )
    stream: bool = Field(
        default=False,
        description="Whether to stream the response",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of relevant documents to retrieve",
    )


# Response models


class QASourceItem(BaseModel):
    """A source document used in the answer."""

    id: str = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    relevance: float = Field(..., description="Relevance score")


class QAResponse(BaseModel):
    """Response model for a QA answer."""

    answer: str = Field(..., description="The generated answer")
    sources: list[QASourceItem] = Field(
        default_factory=list,
        description="Source documents used",
    )
    related_concepts: list[str] = Field(
        default_factory=list,
        description="Related concepts mentioned in the answer",
    )


class SaveQARequest(BaseModel):
    """Request to save a Q&A interaction."""

    question: str = Field(..., min_length=1, description="The question")
    answer: str = Field(..., min_length=1, description="The answer")
    sources: list[str] = Field(default_factory=list, description="Source document IDs")


class SaveQAResponse(BaseModel):
    """Response for saving a Q&A interaction."""

    success: bool
    id: str


class QAHistoryItem(BaseModel):
    """A single Q&A history entry."""

    id: str
    question: str
    answer: str
    sources: list[str] = Field(default_factory=list)
    created_at: str


class QAHistoryResponse(BaseModel):
    """Paginated Q&A history response."""

    total: int
    page: int
    limit: int
    items: list[QAHistoryItem]


router = APIRouter(prefix="/qa", tags=["qa"])


def get_qa_service(
    db: Database = Depends(get_db),
) -> QAService:
    """Create a QAService instance with injected dependencies.

    Args:
        db: Database instance from dependency injection.

    Returns:
        Configured QAService instance.
    """
    doc_repo = DocumentRepo(db)
    llm_client = LLMClient()
    return QAService(doc_repo=doc_repo, llm_client=llm_client)


@router.post("/ask", response_model=None)
async def ask_question(
    request: QARequest,
    user: User = Depends(get_current_user),
    qa_service: QAService = Depends(get_qa_service),
) -> dict | StreamingResponse:
    """Answer a question using relevant documents.

    Requires authentication. Searches for relevant documents and uses
    an LLM to generate an answer. Supports streaming mode via SSE.

    Args:
        request: QA request with question, stream flag, and top_k.
        user: Current authenticated user.
        qa_service: QA service instance.

    Returns:
        QAResponse dict for non-streaming, or SSE StreamingResponse.
    """
    if request.stream:
        return StreamingResponse(
            _stream_response(qa_service, request),
            media_type="text/event-stream",
        )

    try:
        result = await qa_service.ask(
            question=request.question,
            top_k=request.top_k,
        )
    except AppError:
        raise
    except Exception as e:
        logger.error("QA ask failed: %s", e)
        raise AppError(ErrorCode.INTERNAL_ERROR, detail=str(e))

    return result.to_dict()


async def _stream_response(
    qa_service: QAService,
    request: QARequest,
) -> None:
    """Generate SSE events from the streaming QA response.

    Args:
        qa_service: QA service instance.
        request: QA request with question parameters.
    """
    try:
        async for chunk in qa_service.stream_ask(
            question=request.question,
            top_k=request.top_k,
        ):
            data = json.dumps({"chunk": chunk})
            yield f"data: {data}\n\n"
    except AppError as e:
        logger.error("QA streaming failed: %s", e.detail)
        error_data = json.dumps({"error": {"code": e.code, "message": e.message}})
        yield f"data: {error_data}\n\n"
    except Exception as e:
        logger.error("QA streaming failed: %s", e)
        error_data = json.dumps({"error": {"code": "INTERNAL_ERROR", "message": "An unexpected error occurred"}})
        yield f"data: {error_data}\n\n"


@router.post("/save", response_model=SaveQAResponse)
async def save_qa(
    request: SaveQARequest,
    user: User = Depends(get_current_user),
    db: Database = Depends(get_db),
) -> SaveQAResponse:
    """Save a Q&A interaction to the knowledge base.

    Args:
        request: Save request with question, answer, and sources.
        user: Current authenticated user.
        db: Database instance.

    Returns:
        Save result with the QA ID.
    """
    qa_id = str(uuid.uuid4())
    await db.save_qa(
        qa_id=qa_id,
        question=request.question,
        answer=request.answer,
        sources=request.sources,
    )

    return SaveQAResponse(success=True, id=qa_id)


@router.get("/history", response_model=QAHistoryResponse)
async def get_qa_history(
    page: int = 1,
    limit: int = 20,
    user: User = Depends(get_current_user),
    db: Database = Depends(get_db),
) -> QAHistoryResponse:
    """Get Q&A history with pagination.

    Args:
        page: Page number (1-indexed).
        limit: Items per page.
        user: Current authenticated user.
        db: Database instance.

    Returns:
        Paginated Q&A history.
    """
    all_history = await db.get_qa_history(limit=1000)

    # Paginate
    total = len(all_history)
    start = (page - 1) * limit
    end = start + limit
    page_items = all_history[start:end]

    items = [
        QAHistoryItem(
            id=item["id"],
            question=item["question"],
            answer=item["answer"],
            sources=item.get("sources", []),
            created_at=item["created_at"],
        )
        for item in page_items
    ]

    return QAHistoryResponse(
        total=total,
        page=page,
        limit=limit,
        items=items,
    )
