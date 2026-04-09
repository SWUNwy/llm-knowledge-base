from __future__ import annotations
"""Document management router for CRUD and search operations."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.auth.dependencies import get_current_user, get_db
from src.database import Database
from src.models.document import DocumentListResponse, DocumentSummary
from src.models.user import User
from src.repositories.document_repo import DocumentRepo

router = APIRouter(prefix="/documents", tags=["documents"])


# Response models
class DocumentDetail(BaseModel):
    """Detailed document response."""

    id: str = Field(..., description="Document ID")
    type: str = Field(..., description="Document type")
    path: str = Field(..., description="Storage path")
    title: Optional[str] = Field(None, description="Document title")
    status: str = Field(..., description="Processing status")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class DocumentDeleteResponse(BaseModel):
    """Response for document deletion."""

    success: bool = Field(..., description="Whether deletion succeeded")
    message: str = Field(..., description="Status message")


class SearchResponse(BaseModel):
    """Response for document search."""

    total: int = Field(..., description="Total matching documents")
    items: list[dict] = Field(default_factory=list, description="Search results with rank")


def get_document_repo(db: Database = Depends(get_db)) -> DocumentRepo:
    """Create a DocumentRepo instance with injected database.

    Args:
        db: Database instance from dependency injection.

    Returns:
        Configured DocumentRepo instance.
    """
    return DocumentRepo(db)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    type: Optional[str] = Query(None, description="Filter by document type"),
    status: Optional[str] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    user: User = Depends(get_current_user),
    repo: DocumentRepo = Depends(get_document_repo),
) -> DocumentListResponse:
    """List documents with optional type/status filters and pagination.

    Requires authentication.

    Args:
        type: Optional document type filter.
        status: Optional status filter.
        page: Page number (1-based).
        limit: Items per page.
        user: Current authenticated user.
        repo: Document repository instance.

    Returns:
        Paginated list of documents.
    """
    offset = (page - 1) * limit
    documents, total = await repo.list_documents(
        doc_type=type,
        status=status,
        limit=limit,
        offset=offset,
    )

    items = [
        DocumentSummary(
            id=doc["id"],
            title=doc.get("title") or "",
            type=doc["type"],
            status=doc["status"],
            created_at=doc["created_at"],
            tags=doc.get("metadata", {}).get("tags", []),
        )
        for doc in documents
    ]

    return DocumentListResponse(
        total=total,
        page=page,
        limit=limit,
        items=items,
    )


@router.get("/search", response_model=SearchResponse)
async def search_documents(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    user: User = Depends(get_current_user),
    repo: DocumentRepo = Depends(get_document_repo),
) -> SearchResponse:
    """Full-text search across documents.

    Requires authentication. Uses FTS5 for fast full-text search
    across document titles and content.

    Args:
        q: Search query string.
        limit: Maximum number of results.
        user: Current authenticated user.
        repo: Document repository instance.

    Returns:
        Search results with relevance ranking.
    """
    results = await repo.search_documents(query=q, limit=limit)

    items = []
    for doc in results:
        items.append(
            {
                "id": doc["id"],
                "title": doc.get("title", ""),
                "type": doc["type"],
                "status": doc["status"],
                "rank": doc.get("rank", 0),
            }
        )

    return SearchResponse(total=len(items), items=items)


@router.get("/{doc_id}", response_model=DocumentDetail)
async def get_document(
    doc_id: str,
    user: User = Depends(get_current_user),
    repo: DocumentRepo = Depends(get_document_repo),
) -> DocumentDetail:
    """Get a single document by ID.

    Requires authentication.

    Args:
        doc_id: Document ID to retrieve.
        user: Current authenticated user.
        repo: Document repository instance.

    Returns:
        Detailed document information.

    Raises:
        HTTPException: 404 if document not found.
    """
    doc = await repo.get_document(doc_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )

    return DocumentDetail(
        id=doc["id"],
        type=doc["type"],
        path=doc["path"],
        title=doc.get("title"),
        status=doc["status"],
        metadata=doc.get("metadata", {}),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


@router.delete("/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_document(
    doc_id: str,
    user: User = Depends(get_current_user),
    repo: DocumentRepo = Depends(get_document_repo),
) -> DocumentDeleteResponse:
    """Delete a document by ID.

    Requires authentication. Removes the document from both the
    database and the full-text search index.

    Args:
        doc_id: Document ID to delete.
        user: Current authenticated user.
        repo: Document repository instance.

    Returns:
        Deletion confirmation.

    Raises:
        HTTPException: 404 if document not found.
    """
    deleted = await repo.delete_document(doc_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {doc_id}",
        )

    return DocumentDeleteResponse(
        success=True,
        message=f"Document {doc_id} deleted successfully",
    )
