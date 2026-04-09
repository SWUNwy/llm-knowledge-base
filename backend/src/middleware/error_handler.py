from __future__ import annotations
"""Global exception handlers for FastAPI.

Converts all exceptions into a unified JSON response format:

    { "error": { "code": "...", "message": "..." } }
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.errors import AppError, ErrorCode

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the FastAPI app."""

    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        logger.warning("AppError [%s]: %s", exc.code, exc.detail or exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message}},
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR,
                    "message": "Invalid request parameters",
                }
            },
        )

    @app.exception_handler(Exception)
    async def handle_unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR,
                    "message": "An unexpected error occurred",
                }
            },
        )
