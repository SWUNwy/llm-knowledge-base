from __future__ import annotations
"""Unified error types for the application.

Defines error codes and a custom exception class that are shared
between backend and frontend for consistent error handling.
"""

import enum


class ErrorCode(str, enum.Enum):
    """Machine-readable error codes.

    Frontend uses these codes to map user-friendly messages.
    """

    # LLM errors
    LLM_API_KEY_INVALID = "LLM_API_KEY_INVALID"
    LLM_QUOTA_EXCEEDED = "LLM_QUOTA_EXCEEDED"
    LLM_RATE_LIMIT = "LLM_RATE_LIMIT"
    LLM_TIMEOUT = "LLM_TIMEOUT"
    LLM_SERVICE_DOWN = "LLM_SERVICE_DOWN"
    LLM_MODEL_NOT_FOUND = "LLM_MODEL_NOT_FOUND"

    # Import errors
    IMPORT_INVALID_URL = "IMPORT_INVALID_URL"
    IMPORT_FILE_NOT_FOUND = "IMPORT_FILE_NOT_FOUND"
    IMPORT_PARSE_FAILED = "IMPORT_PARSE_FAILED"

    # Auth errors
    AUTH_INVALID_CREDENTIALS = "AUTH_INVALID_CREDENTIALS"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_SETUP_REQUIRED = "AUTH_SETUP_REQUIRED"

    # General errors
    NOT_FOUND = "NOT_FOUND"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"


# User-friendly messages returned by the API.
# Frontend may override these with richer local messages.
DEFAULT_MESSAGES: dict[ErrorCode, str] = {
    ErrorCode.LLM_API_KEY_INVALID: "LLM API Key authentication failed",
    ErrorCode.LLM_QUOTA_EXCEEDED: "LLM API quota exceeded",
    ErrorCode.LLM_RATE_LIMIT: "LLM API rate limit reached",
    ErrorCode.LLM_TIMEOUT: "LLM request timed out",
    ErrorCode.LLM_SERVICE_DOWN: "LLM service is unavailable",
    ErrorCode.LLM_MODEL_NOT_FOUND: "LLM model not found",
    ErrorCode.IMPORT_INVALID_URL: "Invalid or unreachable URL",
    ErrorCode.IMPORT_FILE_NOT_FOUND: "File not found",
    ErrorCode.IMPORT_PARSE_FAILED: "Failed to parse the imported content",
    ErrorCode.AUTH_INVALID_CREDENTIALS: "Invalid username or password",
    ErrorCode.AUTH_TOKEN_EXPIRED: "Session expired, please sign in again",
    ErrorCode.AUTH_SETUP_REQUIRED: "Initial setup required",
    ErrorCode.NOT_FOUND: "Resource not found",
    ErrorCode.VALIDATION_ERROR: "Invalid request parameters",
    ErrorCode.INTERNAL_ERROR: "An unexpected error occurred",
}


class AppError(Exception):
    """Application-level error with structured code and user-friendly message.

    Attributes:
        code: Machine-readable error code for frontend mapping.
        message: User-friendly description (shown in API response).
        detail: Internal detail for server logs (never sent to client).
        status_code: HTTP status code.
    """

    def __init__(
        self,
        code: ErrorCode,
        detail: str = "",
        status_code: int = 500,
    ) -> None:
        self.code = code
        self.message = DEFAULT_MESSAGES.get(code, "An error occurred")
        self.detail = detail
        self.status_code = status_code
        super().__init__(self.message)
