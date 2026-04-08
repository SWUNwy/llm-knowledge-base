"""Compile router for triggering document compilation."""

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.auth.dependencies import get_current_user, get_db
from src.config import Settings, get_settings
from src.database import Database
from src.llm.client import LLMClient
from src.models.user import User
from src.repositories.document_repo import DocumentRepo
from src.services.compile import CompileService


# Request models
class CompileRequest(BaseModel):
    """Request model for document compilation."""

    doc_ids: list[str] = Field(
        ...,
        min_length=1,
        description="List of document IDs to compile",
    )
    output_language: str = Field(
        default="中文",
        description="Output language for the wiki article",
    )


# Response models
class CompileSingleResult(BaseModel):
    """Result of compiling a single document."""

    success: bool = Field(..., description="Whether compilation succeeded")
    doc_id: str = Field(..., description="Document ID")
    wiki_path: Optional[str] = Field(None, description="Path to the wiki article")
    title: Optional[str] = Field(None, description="Document title")
    error: Optional[str] = Field(None, description="Error message if failed")


class CompileResponse(BaseModel):
    """Response model for compilation trigger."""

    task_id: Optional[str] = Field(
        None,
        description="Task ID for async batches (>5 docs)",
    )
    total: int = Field(..., description="Total documents to compile")
    completed: int = Field(default=0, description="Successfully compiled count")
    failed: int = Field(default=0, description="Failed compilation count")
    results: Optional[list[CompileSingleResult]] = Field(
        None,
        description="Individual results (sync mode only)",
    )
    status: str = Field(..., description="Batch status: pending/completed")


class TaskStatusResponse(BaseModel):
    """Response model for task status."""

    id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    total_docs: int = Field(default=0, description="Total documents")
    completed_docs: int = Field(default=0, description="Completed documents")
    failed_docs: int = Field(default=0, description="Failed documents")
    result: Optional[str] = Field(None, description="Result JSON")
    created_at: Optional[str] = Field(None, description="Task creation time")
    completed_at: Optional[str] = Field(None, description="Task completion time")


class TaskListResponse(BaseModel):
    """Response model for listing compile tasks."""

    tasks: list[TaskStatusResponse] = Field(
        default_factory=list,
        description="List of compile tasks",
    )


router = APIRouter(prefix="/compile", tags=["compile"])


def get_compile_service(
    db: Database = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> CompileService:
    """Create a CompileService instance with injected dependencies.

    Args:
        db: Database instance from dependency injection.
        settings: Application settings from dependency injection.

    Returns:
        Configured CompileService instance.
    """
    vault_path = Path(settings.vault_path)
    doc_repo = DocumentRepo(db)
    llm_client = LLMClient()
    return CompileService(
        vault_path=vault_path,
        doc_repo=doc_repo,
        llm_client=llm_client,
        settings=settings,
    )


@router.post("", response_model=CompileResponse)
async def compile_documents(
    request: CompileRequest,
    user: User = Depends(get_current_user),
    compile_service: CompileService = Depends(get_compile_service),
) -> CompileResponse:
    """Trigger compilation of one or more documents.

    Requires authentication. For 5 or fewer documents, compiles
    synchronously and returns results. For more than 5, returns
    a task_id for tracking progress.

    Args:
        request: Compile request with doc_ids and output language.
        user: Current authenticated user.
        compile_service: Compile service instance.

    Returns:
        CompileResponse with results or task_id.
    """
    result = await compile_service.compile_batch(
        doc_ids=request.doc_ids,
        output_language=request.output_language,
    )

    response = CompileResponse(
        total=result.total,
        completed=result.completed,
        failed=result.failed,
        status=result.status,
    )

    if result.task_id:
        response.task_id = result.task_id

    if result.results:
        response.results = [
            CompileSingleResult(**r.to_dict()) for r in result.results
        ]

    return response


@router.get("/tasks/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    user: User = Depends(get_current_user),
    db: Database = Depends(get_db),
) -> TaskStatusResponse:
    """Get the status of a compile task.

    Requires authentication.

    Args:
        task_id: The task ID to look up.
        user: Current authenticated user.
        db: Database instance.

    Returns:
        TaskStatusResponse with current task status.

    Raises:
        HTTPException: 404 if task not found.
    """
    task = await db.get_compile_task(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task not found: {task_id}",
        )

    return TaskStatusResponse(
        id=task["id"],
        status=task["status"],
        total_docs=task["total_docs"],
        completed_docs=task["completed_docs"],
        failed_docs=task["failed_docs"],
        result=task.get("result"),
        created_at=task.get("created_at"),
        completed_at=task.get("completed_at"),
    )


@router.get("/tasks", response_model=TaskListResponse)
async def list_compile_tasks(
    user: User = Depends(get_current_user),
    db: Database = Depends(get_db),
) -> TaskListResponse:
    """List all compile tasks.

    Requires authentication. Returns compile history ordered by
    creation time (most recent first).

    Args:
        user: Current authenticated user.
        db: Database instance.

    Returns:
        TaskListResponse with list of compile tasks.
    """
    async with db._conn.execute(
        "SELECT * FROM compile_tasks ORDER BY created_at DESC"
    ) as cursor:
        rows = await cursor.fetchall()
        tasks = [
            TaskStatusResponse(
                id=row["id"],
                status=row["status"],
                total_docs=row["total_docs"],
                completed_docs=row["completed_docs"],
                failed_docs=row["failed_docs"],
                result=row["result"],
                created_at=row["created_at"],
                completed_at=row["completed_at"],
            )
            for row in rows
        ]

    return TaskListResponse(tasks=tasks)
