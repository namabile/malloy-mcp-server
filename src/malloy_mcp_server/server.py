"""MCP server for executing Malloy queries."""

import json
import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any, cast

from malloy_publisher_client import MalloyAPIClient
from malloy_publisher_client.api_client import APIError
from malloy_publisher_client.models import CompiledModel, Model, Package
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent

from malloy_mcp_server.errors import MalloyError, format_error

# Configure logging
logger = logging.getLogger(__name__)

# Default URL for the Malloy Publisher API
DEFAULT_PUBLISHER_URL = "http://localhost:4000"

# Error messages
ERROR_NO_PROJECTS = "No projects found"
ERROR_NO_PACKAGES = "No packages found"
ERROR_NO_MODELS = "No valid models found"

# Initialize MCP server with minimal capabilities
mcp = FastMCP(
    name="malloy-mcp-server",
    description="MCP server for Malloy queries",
    capabilities={
        "resources": {"subscribelistChanged": True},
        "tools": {"listChanged": True},
    },
)

# Malloy query examples for prompt
MALLOY_EXAMPLES = """
# Basic Malloy query examples:
# Example 1: Simple aggregation
source: orders is table('orders.parquet') extend {
  measure: order_count is count()
  measure: total_revenue is sum(amount)
}
query: orders -> {
  aggregate: order_count, total_revenue
}
# Example 2: Group by with aggregation
query: orders -> {
  group_by: category
  aggregate: order_count, total_revenue
}
"""


# Tools
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
    query = call.parameters["query"]
    client: MalloyAPIClient = call.context["client"]

    try:
        result = client.execute_query(query)
        return result
    except Exception as e:
        error_msg = (
            f"Failed to execute query: {e.message}"
            if isinstance(e, APIError)
            else f"Failed to execute query: {e!s}"
        )
        raise MalloyError(error_msg) from e


# Prompts
@mcp.prompt("malloy")
def create_malloy_query(message: str) -> TextContent:
    """Create a Malloy query from a natural language prompt."""
    return TextContent(
        type="text",
        text=f"Based on these Malloy examples:\n{MALLOY_EXAMPLES}\n"
        f"Create a Malloy query for: {message}",
    )


# Helper functions
def get_publisher_url() -> str:
    """Get the Malloy Publisher URL from environment or use default."""
    return os.environ.get("MALLOY_PUBLISHER_ROOT_URL", DEFAULT_PUBLISHER_URL)


def connect_to_publisher(base_url: str | None = None) -> MalloyAPIClient:
    """Connect to the Malloy Publisher API."""
    url = base_url if base_url is not None else get_publisher_url()

    try:
        client = MalloyAPIClient(url)
        client.list_projects()  # Test connection
        logging.info(f"Connected to Malloy Publisher at {url}")
        return client
    except Exception as e:
        error_msg = (
            f"Failed to connect to Malloy Publisher: {e.message}"
            if isinstance(e, APIError)
            else f"Failed to connect to Malloy Publisher: {e!s}"
        )
        raise MalloyError(error_msg) from e


# Resources
@mcp.resource("packages://{project_name}")
def get_packages(project_name: str) -> list[Package]:
    """Get list of available packages.
    
    Args:
        project_name: Name of the project
        
    Returns:
        list[Package]: List of Malloy packages in the project
    """
    # Access client from the global client instance for simplicity
    # Note: In a production app, you would use a more robust approach
    client = connect_to_publisher()
    packages = client.list_packages(project_name)
    if not packages:
        raise MalloyError(ERROR_NO_PACKAGES)
    return packages


@mcp.resource("models://{project_name}/{package_name}")
def get_models(project_name: str, package_name: str) -> list[Model]:
    """Get models for a package.
    
    Args:
        project_name: Name of the project
        package_name: Name of the package
        
    Returns:
        list[Model]: List of Malloy models in the package
    """
    # Access client from the global client instance for simplicity
    client = connect_to_publisher()
    return client.list_models(project_name, package_name)


@mcp.resource("model://{project_name}/{package_name}/{model_path}")
def get_model(project_name: str, package_name: str, model_path: str) -> CompiledModel:
    """Get details for a specific model.
    
    Args:
        project_name: Name of the project
        package_name: Name of the package
        model_path: Path to the model
        
    Returns:
        CompiledModel: The compiled Malloy model
    """
    # Access client from the global client instance for simplicity
    client = connect_to_publisher()
    # Explicit cast to ensure type compatibility
    return cast(CompiledModel, client.get_model(project_name, package_name, model_path))


@asynccontextmanager
async def app_lifespan(app: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Manage application lifecycle and initialize resources."""
    client = None
    try:
        client = connect_to_publisher()
        projects = client.list_projects()
        
        if not projects:
            raise MalloyError(ERROR_NO_PROJECTS)

        # Get packages for the first project
        try:
            packages = client.list_packages(projects[0].name)
            if not packages:
                raise MalloyError(ERROR_NO_PACKAGES)
        except Exception as e:
            error_msg = f"Failed to list packages: {e!s}"
            raise MalloyError(error_msg) from e

        # Get models for each package
        models = []
        for package in packages:
            try:
                package_models = client.list_models(projects[0].name, package.name)
                models.extend(package_models)
            except Exception as e:
                logger.warning(
                    f"Failed to list models for package {package.name}: {e!s}"
                )

        if not models:
            raise MalloyError(ERROR_NO_MODELS)

        context = {
            "client": client,
            "project_name": projects[0].name,
        }
        
        yield context

    except Exception as e:
        error_msg = format_error(
            e if isinstance(e, MalloyError) else MalloyError(str(e))
        )
        logger.error(error_msg)
        if client:
            client.close()
        raise

    finally:
        if client:
            with suppress(Exception):
                client.close()


# Set lifespan
mcp.settings.lifespan = app_lifespan

# Export the FastMCP instance
__all__ = ["mcp", "create_malloy_query", "execute_malloy_query"]
