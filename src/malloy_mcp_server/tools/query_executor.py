"""Tool for executing Malloy queries via the publisher API."""

from typing import Any, Dict
from molloy_publisher_client import MalloyAPIClient, QueryParams, QueryResult
from mcp.server.context import Context
from mcp.server.errors import ToolError
from mcp.server.fastmcp import FastMCP

# Initialize MCP and client
mcp = FastMCP("Malloy Query Executor")
client = MalloyAPIClient("http://localhost:4000")
PROJECT_NAME = "home"


@mcp.tool()
async def execute_malloy_query(
    query: str, model_path: str, ctx: Context
) -> Dict[str, Any]:
    """Execute a Malloy query.

    Args:
        query: The Malloy query to execute
        model_path: Path to the Malloy model to query against
        ctx: The MCP context for logging and progress tracking

    Returns:
        The query results as a dictionary containing:
        - data_styles: Data style for rendering query results
        - model_def: Malloy model definition
        - query_result: Malloy query results

    Raises:
        ToolError: If query execution fails
    """
    try:
        # Log query execution start
        await ctx.info(f"Executing query against model {model_path}")

        # Execute query via publisher client
        params = QueryParams(
            project_name=PROJECT_NAME,
            package_name="home",  # Default package name
            path=model_path,
            query=query,
        )
        result: QueryResult = client.execute_query(params)

        # Log successful execution
        await ctx.info(f"Query executed successfully")

        # Convert QueryResult to Dict[str, Any]
        return {
            "data_styles": result.data_styles,
            "model_def": result.model_def,
            "query_result": result.query_result,
        }

    except Exception as e:
        error_msg = f"Failed to execute Malloy query: {e!s}"
        await ctx.error(error_msg)
        raise ToolError(
            message=error_msg,
            context={
                "query": query,
                "model_path": model_path,
                "project": PROJECT_NAME,
            },
        ) from e
