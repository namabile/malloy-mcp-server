"""
Malloy MCP Server - a streamlined MCP server for Malloy queries.
"""

__version__ = "0.1.0"

from malloy_mcp_server.server import (
    create_malloy_query,
    execute_malloy_query,
    mcp,
)

__all__ = [
    "create_malloy_query",
    "execute_malloy_query",
    "mcp",
]
