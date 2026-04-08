"""System status router for health and statistics."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from src.auth.dependencies import get_db
from src.database import Database
from src.repositories.document_repo import DocumentRepo

router = APIRouter(prefix="/system", tags=["system"])


class SystemStatus(BaseModel):
    """System status response model."""

    status: str = Field(..., description="System status")
    total_documents: int = Field(..., description="Total number of documents")
    pending_documents: int = Field(..., description="Documents pending processing")
    processed_documents: int = Field(..., description="Fully processed documents")
    wiki_count: int = Field(..., description="Number of wiki entries")


@router.get("/status", response_model=SystemStatus)
async def get_system_status(
    db: Database = Depends(get_db),
) -> SystemStatus:
    """Get system health and statistics.

    Returns overall system status along with document counts.
    No authentication required.

    Args:
        db: Database instance from dependency injection.

    Returns:
        SystemStatus with health and document statistics.
    """
    repo = DocumentRepo(db)

    total = await repo.get_total_document_count()
    pending = await repo.get_document_count_by_status("pending")
    processed = await repo.get_document_count_by_status("processed")
    wiki_count = await repo.get_wiki_count()

    return SystemStatus(
        status="ok",
        total_documents=total,
        pending_documents=pending,
        processed_documents=processed,
        wiki_count=wiki_count,
    )
