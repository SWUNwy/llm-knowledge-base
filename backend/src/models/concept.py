"""Concept models for the knowledge base."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ConceptBase(BaseModel):
    """Base concept model."""

    name: str = Field(..., description="Concept name")
    wiki_path: Optional[str] = Field(None, description="Path to wiki page")
    mention_count: int = Field(0, description="Number of mentions")


class Concept(ConceptBase):
    """Full concept model."""

    id: str = Field(..., description="Concept ID")
    created_at: str = Field(..., description="Creation timestamp")

    class Config:
        from_attributes = True


class ConceptSummary(BaseModel):
    """Summary of a concept for list views."""

    id: str
    name: str
    mention_count: int
    created_at: str


class ConceptListResponse(BaseModel):
    """Paginated concept list response."""

    total: int
    page: int
    limit: int
    items: list[ConceptSummary]
