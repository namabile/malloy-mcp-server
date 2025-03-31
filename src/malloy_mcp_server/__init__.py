"""
Malloy MCP Server - a streamlined MCP server for Malloy queries.
"""

__version__ = "0.1.0"

from malloy_mcp_server.prompts import create_malloy_query
from malloy_mcp_server.server import mcp
from malloy_mcp_server.tools import execute_malloy_query

__all__ = [
    "create_malloy_query",
    "execute_malloy_query",
    "mcp",
]
