"""Malloy MCP server package."""

from .prompts.query_creator import CreateMalloyQueryPrompt
from .server import mcp
from .tools.query_executor import ExecuteMalloyQueryTool

__version__ = "0.1.0"
__all__ = [
    "CreateMalloyQueryPrompt",
    "ExecuteMalloyQueryTool",
    "mcp",
]
