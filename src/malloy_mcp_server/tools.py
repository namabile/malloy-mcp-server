"""Tools for the Malloy MCP Server."""

import json
from dataclasses import dataclass
from typing import Any, Dict, cast
from collections.abc import Awaitable

from malloy_publisher_client import MalloyAPIClient, QueryParams
from mcp.server.fastmcp import Context

from .errors import MalloyError
from .server import mcp


@dataclass
class AppContext:
    """Minimal application context."""

    client: MalloyAPIClient
    project_name: str


@mcp.tool()
async def execute_malloy_query(
    query: str,
    model_path: str,
    ctx: Context[Any, Any],
) -> Dict[str, Any]:
    """Execute a Malloy query.

    Args:
        query: The Malloy query to execute
        model_path: Path to the model in format 'package_name/model_name'
        ctx: The MCP context

    Returns:
        The query results including data styles and model definition

    Raises:
        MalloyError: If the query execution fails
    """
    try:
        # Log query execution
        await ctx.info(f"Executing query against model {model_path}")

        # Get client and project from context
        app_ctx = ctx.request_context.lifespan_context

        # Extract package name from model path
        package_name = model_path.split("/")[0]

        # Prepare query params
        query_params = QueryParams(
            project_name=app_ctx["project_name"],
            package_name=package_name,
            path=model_path,
            query=query,
        )

        # Execute query
        try:
            result = cast(Any, await cast(Awaitable[Any], app_ctx["client"].execute_query(params=query_params)))
        except Exception as e:
            raise MalloyError(
                f"Query execution failed: {str(e)}",
                {
                    "query": query,
                    "model_path": model_path,
                    "project": app_ctx["project_name"],
                    "package": package_name,
                },
            ) from e

        # Parse results
        try:
            data_styles = json.loads(result.data_styles) if result.data_styles else {}
            model_def = json.loads(result.model_def) if result.model_def else {}
            query_result = json.loads(result.query_result)
        except json.JSONDecodeError as e:
            raise MalloyError(
                f"Failed to parse query results: {str(e)}",
                {"model_path": model_path}
            ) from e

        # Log success
        await ctx.info("Query executed successfully")

        return {
            "data_styles": data_styles,
            "model_def": model_def,
            "query_result": query_result,
        }

    except MalloyError:
        raise
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        await ctx.error(error_msg)
        raise MalloyError(error_msg, {
            "query": query,
            "model_path": model_path,
        }) from None
