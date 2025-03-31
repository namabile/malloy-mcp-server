"""Simplified error handling for the Malloy MCP Server."""

from typing import Any


class MalloyError(Exception):
    """Custom error class for Malloy-related errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        """Initialize the error with a message and optional context.

        Args:
            message: Error message
            context: Optional context information
        """
        super().__init__(message)
        self.context = context or {}


def format_error(error: MalloyError) -> str:
    """Format an error message with context.

    Args:
        error: The error to format

    Returns:
        str: Formatted error message
    """
    msg = str(error)
    if error.context:
        msg = f"{msg} (context: {error.context})"
    return msg
