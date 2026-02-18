"""Error handling for OpenFisca MCP tools.

Provides a consistent error schema across all tools, as defined in Phase 1 analysis.
"""

from typing import Any


class MCPError(Exception):
    """Base error for MCP tool errors."""

    def __init__(
        self,
        error_type: str,
        message: str,
        code: int = 400,
        details: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ):
        self.error_type = error_type
        self.message = message
        self.code = code
        self.details = details or {}
        self.suggestions = suggestions or []
        super().__init__(message)

    def to_dict(self) -> dict[str, Any]:
        """Convert to error response dictionary."""
        return {
            "error": {
                "type": self.error_type,
                "code": self.code,
                "message": self.message,
                "details": self.details,
                "suggestions": self.suggestions,
            }
        }


class ValidationError(MCPError):
    """Input validation failed."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ):
        super().__init__(
            error_type="validation_error",
            message=message,
            code=400,
            details=details,
            suggestions=suggestions,
        )


class NotFoundError(MCPError):
    """Resource not found."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ):
        super().__init__(
            error_type="not_found_error",
            message=message,
            code=404,
            details=details,
            suggestions=suggestions,
        )


class DependencyError(MCPError):
    """Circular or spiral dependency detected."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ):
        super().__init__(
            error_type="dependency_error",
            message=message,
            code=500,
            details=details,
            suggestions=suggestions,
        )


class ConnectionError(MCPError):
    """Cannot connect to OpenFisca API."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
    ):
        super().__init__(
            error_type="connection_error",
            message=message,
            code=503,
            details=details,
            suggestions=suggestions or ["Check that the OpenFisca server is running"],
        )


def format_api_error(response_data: dict, status_code: int) -> MCPError:
    """Convert OpenFisca API error response to MCPError."""
    # Simple error format: {"error": "message"}
    if "error" in response_data and isinstance(response_data["error"], str):
        message = response_data["error"]
        if status_code == 404:
            return NotFoundError(message)
        return ValidationError(message)

    # Nested error format: {"path/to/field": "message"}
    # This is used for field-level validation errors
    field_errors = {k: v for k, v in response_data.items() if "/" in k or k != "error"}
    if field_errors:
        first_path = next(iter(field_errors.keys()))
        first_message = field_errors[first_path]
        return ValidationError(
            message=f"Validation error at {first_path}: {first_message}",
            details={"field_errors": field_errors},
            suggestions=["Check the field path and value format"],
        )

    # Unknown format
    return ValidationError(
        message="API returned an error",
        details={"raw_response": response_data},
    )
