"""FastAPI application entry point."""

from pathlib import Path

from fastapi import FastAPI

from src.auth.dependencies import get_db
from src.auth.router import router as auth_router
from src.config import get_settings
from src.database import Database
from src.routers.ingest import router as ingest_router

app = FastAPI(
    title="LLM Knowledge Base",
    description="A local-first LLM-powered knowledge base application",
    version="0.1.0",
)

# Register auth router
app.include_router(auth_router, prefix="/api/v1")

# Register ingest router
app.include_router(ingest_router, prefix="/api/v1")


@app.on_event("startup")
async def startup() -> None:
    """Initialize application on startup."""
    settings = get_settings()
    vault_path = Path(settings.vault_path)
    db_path = vault_path / ".wiki" / "metadata.db"

    # Ensure parent directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize database
    db = Database(db_path)
    await db.connect()
    await db.initialize()

    # Store database in app state
    app.state.db = db

    # Override the get_db dependency to use the app's database
    async def _get_db() -> Database:
        return app.state.db

    app.dependency_overrides[get_db] = _get_db


@app.on_event("shutdown")
async def shutdown() -> None:
    """Clean up on shutdown."""
    if hasattr(app.state, "db"):
        await app.state.db.close()


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
