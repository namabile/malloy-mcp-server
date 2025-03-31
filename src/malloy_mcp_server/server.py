"""MCP server for executing Malloy queries."""

import logging
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any, cast

from malloy_publisher_client import MalloyAPIClient, QueryParams
from malloy_publisher_client.api_client import APIError
from malloy_publisher_client.models import CompiledModel, Model, Package, Project
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
ERROR_QUERY_CONFLICT = (
    "Parameters 'query' and 'query_name' are mutually exclusive - provide only one"
)
ERROR_MISSING_SOURCE_NAME = (
    "Parameter 'source_name' is required when using 'query_name'"
)
ERROR_MISSING_QUERY = "Either 'query' or 'query_name' parameter must be provided"

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
@mcp.tool()
async def execute_malloy_query(
    project_name: str = "home",
    package_name: str = "",
    model_path: str = "",
    query: str = "",
    source_name: str = "",
    query_name: str = "",
    version_id: str = "",  # noqa: ARG001 - Part of API contract
) -> Any:
    """Execute a Malloy query.

    Args:
        project_name: The name of the project, defaults to "home"
        package_name: The name of the package containing the model
        model_path: The path to the model within the package
        query: The Malloy query string to execute (mutually exclusive with query_name)
        source_name: Name of the source in the model (required when using query_name)
        query_name: Name of a query to execute on a source
            (mutually exclusive with query)
        version_id: Version ID of the package

    Returns:
        Any: Query execution result

    Raises:
        MalloyError: If query execution fails or parameters are invalid
    """
    # Input validation
    if query and query_name:
        raise MalloyError(
            ERROR_QUERY_CONFLICT,
            {"query": query, "query_name": query_name},
        )

    if query_name and not source_name:
        raise MalloyError(
            ERROR_MISSING_SOURCE_NAME,
            {"query_name": query_name, "source_name": source_name},
        )

    # The context is injected by the framework but isn't part of our function signature
    # Get client - the MCP framework will connect to publisher if needed
    client = connect_to_publisher()

    try:
        # Execute the query based on the provided parameters
        # Clean up empty parameters
        params = {
            "path": model_path,
            "project_name": project_name,
            "package_name": package_name,
            "query": query,
            "source_name": source_name,
            "query_name": query_name,
        }

        # Only include non-empty parameters
        params = {k: v for k, v in params.items() if v}

        # Pass parameters as QueryParams object
        result = client.execute_query(QueryParams(**params))
        return result
    except Exception as e:
        error_msg = (
            f"Failed to execute query: {e.message}"
            if isinstance(e, APIError)
            else f"Failed to execute query: {e!s}"
        )
        raise MalloyError(
            error_msg,
            {
                "project_name": project_name,
                "package_name": package_name,
                "model_path": model_path,
                "query": query,
                "source_name": source_name,
                "query_name": query_name,
            },
        ) from e


@mcp.tool()
async def list_projects() -> list[Project]:
    """List available projects.

    This tool doesn't require any input parameters.

    Returns:
        list[Project]: List of Malloy projects
    """
    client = connect_to_publisher()
    try:
        projects = client.list_projects()
        if not projects:
            return []
        return projects
    except Exception as e:
        error_msg = (
            f"Failed to list projects: {e.message}"
            if isinstance(e, APIError)
            else f"Failed to list projects: {e!s}"
        )
        raise MalloyError(error_msg) from e


@mcp.tool()
async def list_packages(project_name: str = "home") -> list[Package]:
    """List packages for a project.

    Args:
        project_name: The name of the project to list packages for, defaults to "home"

    Returns:
        list[Package]: List of Malloy packages
    """
    client = connect_to_publisher()
    try:
        packages = client.list_packages(project_name)
        if not packages:
            return []
        return packages
    except Exception as e:
        error_msg = (
            f"Failed to list packages: {e.message}"
            if isinstance(e, APIError)
            else f"Failed to list packages: {e!s}"
        )
        raise MalloyError(error_msg, {"project_name": project_name}) from e


@mcp.tool()
async def list_models(
    project_name: str = "home",
    package_name: str = "",
) -> list[Model]:
    """List models for a package.

    Args:
        project_name: The name of the project, defaults to "home"
        package_name: The name of the package to list models for

    Returns:
        List[Model]: List of Malloy models
    """
    client = connect_to_publisher()
    try:
        models = client.list_models(project_name, package_name)
        return models
    except Exception as e:
        error_msg = (
            f"Failed to list models: {e.message}"
            if isinstance(e, APIError)
            else f"Failed to list models: {e!s}"
        )
        context = {"project_name": project_name, "package_name": package_name}
        raise MalloyError(error_msg, context) from e


@mcp.tool()
async def get_model(
    project_name: str = "home",
    package_name: str = "",
    model_path: str = "",
) -> CompiledModel:
    """Get details for a specific model.

    Args:
        project_name: The name of the project, defaults to "home"
        package_name: The name of the package
        model_path: The path to the model

    Returns:
        CompiledModel: The compiled Malloy model
    """
    client = connect_to_publisher()
    try:
        model = client.get_model(project_name, package_name, model_path)
        return cast(CompiledModel, model)
    except Exception as e:
        error_msg = (
            f"Failed to get model: {e.message}"
            if isinstance(e, APIError)
            else f"Failed to get model: {e!s}"
        )
        context = {
            "project_name": project_name,
            "package_name": package_name,
            "model_path": model_path,
        }
        raise MalloyError(error_msg, context) from e


# Prompts
@mcp.prompt()
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
@mcp.resource("projects://home")
def get_projects() -> list[Project]:
    """Get list of available projects.

    Returns:
        list[Project]: List of project metadata
    """
    client = connect_to_publisher()
    projects = client.list_projects()
    if not projects:
        raise MalloyError(ERROR_NO_PROJECTS)
    return projects


@asynccontextmanager
async def app_lifespan(_app: FastMCP) -> AsyncIterator[dict[str, Any]]:
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
__all__ = [
    "create_malloy_query",
    "execute_malloy_query",
    "get_model",
    "list_models",
    "list_packages",
    "list_projects",
    "mcp",
]
