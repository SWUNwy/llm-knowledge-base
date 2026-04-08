"""Settings router for configuration management."""

import traceback
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.auth.dependencies import get_current_user, get_db
from src.config import Settings, get_settings
from src.database import Database
from src.models.user import User


router = APIRouter(prefix="/settings", tags=["settings"])


class SettingsResponse(BaseModel):
    """Current settings response."""

    llm_default_model: str
    auto_compile: bool
    compile_batch_size: int
    max_concurrent_tasks: int
    llm_providers: dict = Field(default_factory=dict)


class UpdateSettingsRequest(BaseModel):
    """Request to update settings."""

    llm_default_model: Optional[str] = None
    auto_compile: Optional[bool] = None
    compile_batch_size: Optional[int] = None
    max_concurrent_tasks: Optional[int] = None
    gemini_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    ollama_base_url: Optional[str] = None


class VerifyLLMRequest(BaseModel):
    """Request to verify LLM connection."""

    model: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None


class VerifyLLMResult(BaseModel):
    """Result of LLM connection verification."""

    success: bool
    message: str
    latency_ms: Optional[float] = None


@router.get("", response_model=SettingsResponse)
async def get_settings_endpoint(
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> SettingsResponse:
    """Get current settings.

    Args:
        user: Current authenticated user.
        settings: Application settings.

    Returns:
        Current settings (API keys are masked).
    """
    # Build providers dict showing which are configured
    providers = {}
    if settings.gemini_api_key:
        providers["gemini"] = {"configured": True, "key": "****" + settings.gemini_api_key[-4:]}
    if settings.openai_api_key:
        providers["openai"] = {"configured": True, "key": "****" + settings.openai_api_key[-4:]}
    if settings.anthropic_api_key:
        providers["anthropic"] = {"configured": True, "key": "****" + settings.anthropic_api_key[-4:]}
    if settings.ollama_base_url:
        providers["ollama"] = {"configured": True, "base_url": settings.ollama_base_url}

    return SettingsResponse(
        llm_default_model=settings.llm_default_model,
        auto_compile=settings.auto_compile,
        compile_batch_size=settings.compile_batch_size,
        max_concurrent_tasks=settings.max_concurrent_tasks,
        llm_providers=providers,
    )


@router.put("", response_model=SettingsResponse)
async def update_settings(
    request: UpdateSettingsRequest,
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> SettingsResponse:
    """Update settings.

    Updates are written to the .env file. Requires authentication.

    Args:
        request: Settings update request.
        user: Current authenticated user.
        settings: Application settings.

    Returns:
        Updated settings.
    """
    # Read existing .env content
    env_path = settings.model_config.get("env_file", ".env")
    from pathlib import Path

    env_file = Path(env_path)
    lines: list[str] = []
    if env_file.exists():
        lines = env_file.read_text(encoding="utf-8").splitlines()

    # Map request fields to env var names
    env_mapping = {
        "llm_default_model": "LLM_DEFAULT_MODEL",
        "auto_compile": "AUTO_COMPILE",
        "compile_batch_size": "COMPILE_BATCH_SIZE",
        "max_concurrent_tasks": "MAX_CONCURRENT_TASKS",
        "gemini_api_key": "GEMINI_API_KEY",
        "openai_api_key": "OPENAI_API_KEY",
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "ollama_base_url": "OLLAMA_BASE_URL",
    }

    # Update .env file with new values
    updated_keys: set[str] = set()
    new_lines: list[str] = []

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            new_lines.append(line)
            continue

        key = stripped.split("=", 1)[0].strip()
        matched = False
        for field_name, env_key in env_mapping.items():
            if key == env_key:
                value = getattr(request, field_name, None)
                if value is not None:
                    new_lines.append(f"{env_key}={value}")
                    updated_keys.add(env_key)
                    matched = True
                    break
        if not matched:
            new_lines.append(line)

    # Add any new keys that weren't in the file
    for field_name, env_key in env_mapping.items():
        if env_key not in updated_keys:
            value = getattr(request, field_name, None)
            if value is not None:
                new_lines.append(f"{env_key}={value}")

    env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Clear the cached settings so next call picks up changes
    get_settings.cache_clear()

    # Return updated settings
    updated_settings = get_settings()
    return SettingsResponse(
        llm_default_model=updated_settings.llm_default_model,
        auto_compile=updated_settings.auto_compile,
        compile_batch_size=updated_settings.compile_batch_size,
        max_concurrent_tasks=updated_settings.max_concurrent_tasks,
    )


@router.post("/verify-llm", response_model=VerifyLLMResult)
async def verify_llm(
    request: VerifyLLMRequest,
    user: User = Depends(get_current_user),
    settings: Settings = Depends(get_settings),
) -> VerifyLLMResult:
    """Verify LLM connection.

    Tests the connection to the configured LLM provider by sending
    a simple completion request.

    Args:
        request: Verification request with optional model override.
        user: Current authenticated user.
        settings: Application settings.

    Returns:
        Verification result with latency.
    """
    import time

    try:
        import litellm

        model = request.model or settings.llm_default_model

        # Build kwargs for litellm
        kwargs: dict = {
            "model": model,
            "messages": [{"role": "user", "content": "Say 'OK'"}],
            "max_tokens": 5,
        }

        if request.api_key:
            kwargs["api_key"] = request.api_key
        if request.base_url:
            kwargs["api_base"] = request.base_url

        start = time.time()
        response = await litellm.acompletion(**kwargs)
        latency = (time.time() - start) * 1000

        return VerifyLLMResult(
            success=True,
            message=f"Successfully connected to {model}",
            latency_ms=round(latency, 2),
        )
    except Exception as e:
        return VerifyLLMResult(
            success=False,
            message=f"Connection failed: {str(e)}",
        )
