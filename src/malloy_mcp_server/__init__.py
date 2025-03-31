"""
Malloy MCP Server - a streamlined MCP server for Malloy queries.
"""

__version__ = "0.1.0"

from .server import mcp
from .tools import execute_malloy_query
from .prompts import create_malloy_query

__all__ = [
    "mcp",
    "execute_malloy_query",
    "create_malloy_query",
]
