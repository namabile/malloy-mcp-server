"""
Malloy MCP Server - a streamlined MCP server for Malloy queries.
"""

import logging
import sys

__version__ = "0.1.0"

from malloy_mcp_server.server import (
    create_malloy_query,
    execute_malloy_query,
    get_model,
    list_models,
    list_packages,
    list_projects,
    mcp,
)

# Configure logging
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the MCP server."""
    # Configure stderr logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    # Log startup information
    logger.info("Starting Malloy MCP Server...")

    # Run the MCP server with stdio transport
    mcp.run(transport="stdio")


__all__ = [
    "create_malloy_query",
    "execute_malloy_query",
    "get_model",
    "list_models",
    "list_packages",
    "list_projects",
    "mcp",
]
