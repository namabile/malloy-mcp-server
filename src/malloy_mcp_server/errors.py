"""Simplified error handling for the Malloy MCP Server.

This module provides standardized error handling for the Malloy MCP Server,
including error codes, detailed error messages, and context information.

Error Codes:
- MALLOY_ERROR: Generic error
- CONNECTION_ERROR: Error connecting to Malloy Publisher API
- QUERY_EXECUTION_ERROR: Error executing Malloy query
- INVALID_PARAMETERS: Invalid parameters provided
- NOT_FOUND: Requested resource not found
- APP_LIFECYCLE_ERROR: Error during application lifecycle
"""

from typing import Any


class MalloyError(Exception):
    """Custom error class for Malloy-related errors.

    This class provides a standardized way to represent errors in the Malloy MCP Server,
    including error codes, detailed error messages, and context information.

    Attributes:
        message: Detailed error message
        code: Error code identifying the error type
        context: Optional context information about the error
    """

    def __init__(
        self,
        message: str,
        context: dict[str, Any] | None = None,
        code: str = "MALLOY_ERROR",
    ) -> None:
        """Initialize the error with a message, optional context, and error code.

        Args:
            message: Detailed error message
            context: Optional context information about the error
            code: Error code identifying the error type. Default is "MALLOY_ERROR".
                  Should be one of the predefined codes:
                  - MALLOY_ERROR: Generic error
                  - CONNECTION_ERROR: Error connecting to Malloy Publisher API
                  - QUERY_EXECUTION_ERROR: Error executing Malloy query
                  - INVALID_PARAMETERS: Invalid parameters provided
                  - NOT_FOUND: Requested resource not found
                  - APP_LIFECYCLE_ERROR: Error during application lifecycle
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary format.

        Returns:
            dict[str, Any]: Error as dictionary with code, message, and context
        """
        return {"code": self.code, "message": self.message, "context": self.context}


def format_error(error: MalloyError) -> str:
    """Format an error message with context.

    This function formats an error message by including the error code,
    message, and any context information.

    Args:
        error: The error to format

    Returns:
        str: Formatted error message
    """
    msg = f"[{error.code}] {error.message}"
    if error.context:
        msg = f"{msg} (context: {error.context})"
    return msg
