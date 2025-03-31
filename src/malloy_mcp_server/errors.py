"""Simplified error handling for the Malloy MCP Server."""

from typing import Any, Dict


class MalloyError(Exception):
    """Base exception for all Malloy MCP Server errors."""

    def __init__(self, message: str, context: Dict[str, Any] | None = None) -> None:
        """Initialize the error with a message and optional context.

        Args:
            message: Human-readable error message
            context: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.context = context or {}


def format_error(error: MalloyError) -> str:
    """Format an error message with its context.

    Args:
        error: The error to format

    Returns:
        A formatted error message string
    """
    message = f"Error: {error.message}"
    if error.context:
        context_str = "\n".join(f"  {k}: {v}" for k, v in error.context.items())
        message = f"{message}\nContext:\n{context_str}"
    return message
