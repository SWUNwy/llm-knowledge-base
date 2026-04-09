from __future__ import annotations
"""Concepts router for managing knowledge base concepts."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.auth.dependencies import get_current_user, get_db
from src.database import Database
from src.models.concept import Concept, ConceptListResponse, ConceptSummary
from src.models.user import User
from src.repositories.concept_repo import ConceptRepo


router = APIRouter(prefix="/concepts", tags=["concepts"])


class ConceptDetailResponse(BaseModel):
    """Detailed concept response with related documents."""

    id: str
    name: str
    wiki_path: Optional[str] = None
    mention_count: int = 0
    created_at: str
    related_documents: list[dict] = Field(default_factory=list)


@router.get("", response_model=ConceptListResponse)
async def list_concepts(
    page: int = 1,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Database = Depends(get_db),
) -> ConceptListResponse:
    """List all concepts with pagination.

    Args:
        page: Page number (1-indexed).
        limit: Items per page.
        user: Current authenticated user.
        db: Database instance.

    Returns:
        Paginated list of concepts.
    """
    repo = ConceptRepo(db)
    concepts, total = await repo.list_all(page=page, limit=limit)

    items = [
        ConceptSummary(
            id=c["id"],
            name=c["name"],
            mention_count=c.get("mention_count", 0),
            created_at=c["created_at"],
        )
        for c in concepts
    ]

    return ConceptListResponse(
        total=total,
        page=page,
        limit=limit,
        items=items,
    )


@router.get("/{concept_id}", response_model=ConceptDetailResponse)
async def get_concept(
    concept_id: str,
    user: User = Depends(get_current_user),
    db: Database = Depends(get_db),
) -> ConceptDetailResponse:
    """Get concept details by ID.

    Args:
        concept_id: The concept ID.
        user: Current authenticated user.
        db: Database instance.

    Returns:
        Concept details with related documents.

    Raises:
        HTTPException: 404 if concept not found.
    """
    repo = ConceptRepo(db)
    concept = await repo.get_by_id(concept_id)

    if not concept:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Concept not found: {concept_id}",
        )

    return ConceptDetailResponse(
        id=concept["id"],
        name=concept["name"],
        wiki_path=concept.get("wiki_path"),
        mention_count=concept.get("mention_count", 0),
        created_at=concept["created_at"],
        related_documents=[],
    )
