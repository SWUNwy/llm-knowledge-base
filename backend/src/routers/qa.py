"""QA router for question-answering endpoints."""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.auth.dependencies import get_current_user, get_db
from src.database import Database
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
    except Exception as e:
        logger.error(f"QA ask failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate answer: {e}",
        )

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
    except Exception as e:
        logger.error(f"QA streaming failed: {e}")
        error_data = json.dumps({"error": str(e)})
        yield f"data: {error_data}\n\n"
