"""Ingest router for importing documents from URLs and files."""

import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.auth.dependencies import get_current_user, get_db
from src.config import Settings, get_settings
from src.database import Database
from src.models.user import User
from src.services.ingest import IngestService


# Request models
class IngestURLRequest(BaseModel):
    """Request model for URL import."""

    url: str = Field(..., description="URL to import content from")
    tags: list[str] = Field(default_factory=list, description="Tags for the document")


class IngestFileRequest(BaseModel):
    """Request model for local file import."""

    path: str = Field(..., description="Path to the local file to import")
    tags: list[str] = Field(default_factory=list, description="Tags for the document")


class IngestVideoRequest(BaseModel):
    """Request model for video import."""

    url: str = Field(..., description="Video URL (YouTube or Bilibili)")
    tags: list[str] = Field(default_factory=list, description="Tags for the document")


class IngestGithubRequest(BaseModel):
    """Request model for GitHub repository import."""

    repo_url: str = Field(..., description="GitHub repository URL")
    branch: str = Field(default="main", description="Branch to clone")
    tags: list[str] = Field(default_factory=list, description="Tags for the document")


class BatchItem(BaseModel):
    """Single item in a batch import request."""

    type: str = Field(..., description="Import type: url, file, video, github")
    source: str = Field(..., description="URL or path to import")
    tags: list[str] = Field(default_factory=list, description="Tags for the document")


class IngestBatchRequest(BaseModel):
    """Request model for batch import."""

    items: list[BatchItem] = Field(..., min_length=1, description="Items to import")


class IngestStatusResponse(BaseModel):
    """Response model for import status."""

    id: str
    status: str
    progress: int = 100
    error: Optional[str] = None


# Response model
class IngestResponse(BaseModel):
    """Response model for ingest operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    doc_id: Optional[str] = Field(None, description="Document ID if successful")
    title: Optional[str] = Field(None, description="Document title")
    path: Optional[str] = Field(None, description="Storage path")
    error: Optional[str] = Field(None, description="Error message if failed")


class BatchImportResponse(BaseModel):
    """Response model for batch import."""

    batch_id: str
    total: int
    items: list[IngestResponse]


router = APIRouter(prefix="/ingest", tags=["ingest"])


def get_ingest_service(
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> IngestService:
    """Create an IngestService instance with injected dependencies."""
    return IngestService(db=db, settings=settings)


@router.post("/url", response_model=IngestResponse)
async def ingest_url(
    request: IngestURLRequest,
    user: User = Depends(get_current_user),
    ingest_service: IngestService = Depends(get_ingest_service),
) -> IngestResponse:
    """Import content from a URL."""
    result = await ingest_service.ingest_url(
        url=request.url,
        tags=request.tags if request.tags else None,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
        )

    return IngestResponse(**result.to_dict())


@router.post("/file", response_model=IngestResponse)
async def ingest_file(
    request: IngestFileRequest,
    user: User = Depends(get_current_user),
    ingest_service: IngestService = Depends(get_ingest_service),
) -> IngestResponse:
    """Import content from a local file."""
    file_path = Path(request.path)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File not found: {request.path}",
        )

    result = await ingest_service.ingest_file(
        path=request.path,
        tags=request.tags if request.tags else None,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
        )

    return IngestResponse(**result.to_dict())


@router.post("/video", response_model=IngestResponse)
async def ingest_video(
    request: IngestVideoRequest,
    user: User = Depends(get_current_user),
    ingest_service: IngestService = Depends(get_ingest_service),
) -> IngestResponse:
    """Import content from a video URL (YouTube/Bilibili)."""
    result = await ingest_service.ingest_video(
        url=request.url,
        tags=request.tags if request.tags else None,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
        )

    return IngestResponse(**result.to_dict())


@router.post("/github", response_model=IngestResponse)
async def ingest_github(
    request: IngestGithubRequest,
    user: User = Depends(get_current_user),
    ingest_service: IngestService = Depends(get_ingest_service),
) -> IngestResponse:
    """Import content from a GitHub repository."""
    result = await ingest_service.ingest_github(
        repo_url=request.repo_url,
        tags=request.tags if request.tags else None,
    )

    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.error,
        )

    return IngestResponse(**result.to_dict())


@router.post("/batch", response_model=BatchImportResponse)
async def ingest_batch(
    request: IngestBatchRequest,
    user: User = Depends(get_current_user),
    ingest_service: IngestService = Depends(get_ingest_service),
) -> BatchImportResponse:
    """Batch import from multiple sources."""
    batch_id = str(uuid.uuid4())
    results: list[IngestResponse] = []

    for item in request.items:
        result = None
        tags = item.tags if item.tags else None

        if item.type == "url":
            r = await ingest_service.ingest_url(url=item.source, tags=tags)
            result = IngestResponse(**r.to_dict())
        elif item.type == "file":
            r = await ingest_service.ingest_file(path=item.source, tags=tags)
            result = IngestResponse(**r.to_dict())
        elif item.type == "video":
            r = await ingest_service.ingest_video(url=item.source, tags=tags)
            result = IngestResponse(**r.to_dict())
        elif item.type == "github":
            r = await ingest_service.ingest_github(repo_url=item.source, tags=tags)
            result = IngestResponse(**r.to_dict())
        else:
            result = IngestResponse(
                success=False, error=f"Unknown import type: {item.type}"
            )

        results.append(result)

    return BatchImportResponse(
        batch_id=batch_id,
        total=len(results),
        items=results,
    )


@router.get("/status/{import_id}", response_model=IngestStatusResponse)
async def get_import_status(
    import_id: str,
    user: User = Depends(get_current_user),
    db: Database = Depends(get_db),
) -> IngestStatusResponse:
    """Get the status of an import operation."""
    # Check if document exists (completed import)
    doc = await db.get_document(import_id)
    if doc:
        return IngestStatusResponse(
            id=import_id,
            status="completed",
            progress=100,
        )

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Import not found: {import_id}",
    )
