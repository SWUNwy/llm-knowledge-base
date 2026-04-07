"""Ingest router for importing documents from URLs and files."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, HttpUrl

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


# Response model
class IngestResponse(BaseModel):
    """Response model for ingest operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    doc_id: Optional[str] = Field(None, description="Document ID if successful")
    title: Optional[str] = Field(None, description="Document title")
    path: Optional[str] = Field(None, description="Storage path")
    error: Optional[str] = Field(None, description="Error message if failed")


router = APIRouter(prefix="/ingest", tags=["ingest"])


def get_ingest_service(
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> IngestService:
    """Create an IngestService instance with injected dependencies.

    Args:
        db: Database instance from dependency injection.
        settings: Application settings from dependency injection.

    Returns:
        Configured IngestService instance.
    """
    return IngestService(db=db, settings=settings)


@router.post("/url", response_model=IngestResponse)
async def ingest_url(
    request: IngestURLRequest,
    user: User = Depends(get_current_user),
    ingest_service: IngestService = Depends(get_ingest_service),
) -> IngestResponse:
    """Import content from a URL.

    Requires authentication. Parses the content from the given URL,
    saves it to the vault, and creates a database record.

    Args:
        request: URL import request with URL and optional tags.
        user: Current authenticated user.
        ingest_service: Ingest service instance.

    Returns:
        IngestResponse with the result of the import.
    """
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
    """Import content from a local file.

    Requires authentication. Parses the content from the given file,
    saves it to the vault, and creates a database record.

    Args:
        request: File import request with path and optional tags.
        user: Current authenticated user.
        ingest_service: Ingest service instance.

    Returns:
        IngestResponse with the result of the import.

    Raises:
        HTTPException: 404 if the file does not exist.
    """
    # Check if file exists before calling service
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
