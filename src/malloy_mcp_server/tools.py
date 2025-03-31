"""Tools for executing Malloy queries."""

import logging
from typing import Any

from malloy_publisher_client import MalloyAPIClient
from malloy_publisher_client.api_client import APIError

from malloy_mcp_server.errors import MalloyError
from malloy_mcp_server.server import mcp

# Configure logging
logger = logging.getLogger(__name__)


@mcp.tool("execute_malloy_query")
async def execute_malloy_query(call: Any) -> Any:
    """Execute a Malloy query.

    Args:
        call: Tool call containing query parameters

    Returns:
        Any: Query execution result

    Raises:
        MalloyError: If query execution fails
    """
    # Extract parameters
    query = call.parameters["query"]

    # Get client from context
    client: MalloyAPIClient = call.context["client"]

    try:
        # Execute query
        result = client.execute_query(query)
        return result

    except Exception as e:
        error_msg = (
            f"Failed to execute query: {e.message}"
            if isinstance(e, APIError)
            else f"Failed to execute query: {e!s}"
        )
        raise MalloyError(error_msg) from e


# Export tools
__all__ = ["execute_malloy_query"]
