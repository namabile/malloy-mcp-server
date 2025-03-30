"""Tool for executing Malloy queries via the publisher API."""

from typing import Any, cast
import json

from malloy_publisher_client import MalloyAPIClient, QueryParams, QueryResult
from mcp.server.fastmcp import Context
from pydantic import BaseModel

from ..server import mcp


class QueryInput(BaseModel):
    """Input parameters for query execution."""
    query: str
    model_path: str


class QueryOutput(BaseModel):
    """Output from query execution."""
    data_styles: dict[str, Any]
    model_def: dict[str, Any]
    query_result: list[dict[str, Any]]


@mcp.tool()
async def execute_malloy_query(
    params: QueryInput,
    ctx: Context,
) -> QueryOutput:
    """Execute a Malloy query.

    Args:
        params: The query parameters including query string and model path
        ctx: The MCP context for logging and progress tracking

    Returns:
        The query results including data styles and model definition

    Raises:
        ValueError: If query execution fails
    """
    try:
        # Log query execution start
        await ctx.info(f"Executing query against model {params.model_path}")
        await ctx.report_progress(0, 2)

        # Get client from lifespan context
        app_ctx = ctx.request_context.lifespan_context

        # Extract package name from model path (first component)
        package_name = params.model_path.split("/")[0]

        # Execute query via publisher client
        query_params = QueryParams(
            project_name="home",  # Default project name
            package_name=package_name,
            path=params.model_path,
            query=params.query,
        )

        # Execute query
        await ctx.report_progress(1, 2)
        result = cast(QueryResult, await app_ctx.client.execute_query(params=query_params))

        # Parse JSON responses
        data_styles = json.loads(result.data_styles) if result.data_styles else {}
        model_def = json.loads(result.model_def) if result.model_def else {}
        query_result = json.loads(result.query_result) if result.query_result else []

        # Log successful execution
        await ctx.info("Query executed successfully")
        await ctx.report_progress(2, 2)

        return QueryOutput(
            data_styles=data_styles,
            model_def=model_def,
            query_result=query_result,
        )

    except Exception as e:
        error_msg = f"Failed to execute Malloy query: {str(e)}"
        error_context = {
            "query": params.query,
            "model_path": params.model_path,
            "project": "home",
            "package": package_name,
        }
        await ctx.error(f"{error_msg}\nContext: {error_context}")
        raise ValueError(error_msg) from None


# Export the tool function
ExecuteMalloyQueryTool = execute_malloy_query

__all__ = ["ExecuteMalloyQueryTool"]
