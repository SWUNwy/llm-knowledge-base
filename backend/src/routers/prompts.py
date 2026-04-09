from __future__ import annotations
"""Prompts router for managing prompt templates."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.auth.dependencies import get_current_user
from src.llm.prompts import PromptTemplates
from src.models.user import User


router = APIRouter(prefix="/prompts", tags=["prompts"])


class PromptTemplateResponse(BaseModel):
    """Prompt template response."""

    id: str
    name: str
    description: str
    template: str
    is_custom: bool = False


class PromptTemplateList(BaseModel):
    """List of prompt templates."""

    items: list[PromptTemplateResponse]


class UpdatePromptRequest(BaseModel):
    """Request to update a prompt template."""

    template: str = Field(..., min_length=10, description="New template text")


# Default templates
DEFAULT_TEMPLATES = {
    "compile": {
        "name": "Document Compilation",
        "description": "Compile raw documents into structured wiki articles",
        "template": PromptTemplates.COMPILE_DOCUMENT,
    },
    "extract_concepts": {
        "name": "Concept Extraction",
        "description": "Extract key concepts from document content",
        "template": PromptTemplates.EXTRACT_CONCEPTS,
    },
    "qa_answer": {
        "name": "Q&A Answer Generation",
        "description": "Generate answers based on retrieved context",
        "template": PromptTemplates.QA_ANSWER,
    },
}

# Custom template overrides (in-memory for now)
_custom_templates: dict[str, str] = {}


@router.get("", response_model=PromptTemplateList)
async def list_prompts(
    user: User = Depends(get_current_user),
) -> PromptTemplateList:
    """List all prompt templates."""
    items = []
    for template_id, info in DEFAULT_TEMPLATES.items():
        is_custom = template_id in _custom_templates
        template_text = _custom_templates.get(template_id, info["template"])
        items.append(
            PromptTemplateResponse(
                id=template_id,
                name=info["name"],
                description=info["description"],
                template=template_text,
                is_custom=is_custom,
            )
        )

    return PromptTemplateList(items=items)


@router.get("/{template_id}", response_model=PromptTemplateResponse)
async def get_prompt(
    template_id: str,
    user: User = Depends(get_current_user),
) -> PromptTemplateResponse:
    """Get a specific prompt template."""
    if template_id not in DEFAULT_TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found: {template_id}",
        )

    info = DEFAULT_TEMPLATES[template_id]
    is_custom = template_id in _custom_templates
    template_text = _custom_templates.get(template_id, info["template"])

    return PromptTemplateResponse(
        id=template_id,
        name=info["name"],
        description=info["description"],
        template=template_text,
        is_custom=is_custom,
    )


@router.put("/{template_id}", response_model=PromptTemplateResponse)
async def update_prompt(
    template_id: str,
    request: UpdatePromptRequest,
    user: User = Depends(get_current_user),
) -> PromptTemplateResponse:
    """Update a prompt template with custom text."""
    if template_id not in DEFAULT_TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found: {template_id}",
        )

    _custom_templates[template_id] = request.template

    info = DEFAULT_TEMPLATES[template_id]
    return PromptTemplateResponse(
        id=template_id,
        name=info["name"],
        description=info["description"],
        template=request.template,
        is_custom=True,
    )


@router.delete("/{template_id}", response_model=PromptTemplateResponse)
async def reset_prompt(
    template_id: str,
    user: User = Depends(get_current_user),
) -> PromptTemplateResponse:
    """Reset a prompt template to its default."""
    if template_id not in DEFAULT_TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template not found: {template_id}",
        )

    _custom_templates.pop(template_id, None)

    info = DEFAULT_TEMPLATES[template_id]
    return PromptTemplateResponse(
        id=template_id,
        name=info["name"],
        description=info["description"],
        template=info["template"],
        is_custom=False,
    )
