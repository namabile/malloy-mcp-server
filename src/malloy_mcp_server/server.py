"""MCP server for executing Malloy queries."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any, Dict, cast
import json

from malloy_publisher_client import (
    MalloyAPIClient,
    Model,
    Package,
    Project,
)
from malloy_publisher_client.models import CompiledModel
from mcp.server.fastmcp import FastMCP
from malloy_publisher_client.api_client import APIError

from malloy_mcp_server.errors import MalloyError, format_error

# Configure logging
logger = logging.getLogger(__name__)

# Initialize MCP server with minimal capabilities
mcp = FastMCP(
    name="malloy-mcp-server",
    description="MCP server for Malloy queries",
    # Only declare capabilities actually used
    capabilities={
        "resources": {"subscribelistChanged": True},
        "tools": {"listChanged": True},
    },
)


def connect_to_publisher(base_url: str) -> MalloyAPIClient:
    """Connect to the Malloy Publisher API.

    Args:
        base_url: Base URL of the API server

    Returns:
        MalloyAPIClient: Connected API client

    Raises:
        MalloyError: If connection fails
    """
    try:
        client = MalloyAPIClient(base_url)
        # Test connection with a simple API call
        client.list_projects()
        logging.info(f"Connected to Malloy Publisher at {base_url}")
        return client
    except Exception as e:
        if isinstance(e, APIError):
            raise MalloyError(f"Failed to connect to Malloy Publisher: {e.message}") from e
        raise MalloyError(f"Failed to connect to Malloy Publisher: {str(e)}") from e


async def load_packages(client: MalloyAPIClient, project: Project) -> list[Package]:
    """Load packages from the Malloy publisher.

    Args:
        client: The Malloy API client
        project: The project to load packages from

    Returns:
        list[Package]: List of packages

    Raises:
        MalloyError: If packages cannot be loaded
    """
    try:
        packages = client.list_packages(project.name)
        logging.info(f"Loaded {len(packages)} packages from project {project.name}")
        return packages
    except Exception as e:
        if isinstance(e, APIError):
            raise MalloyError(f"Failed to load packages: {e.message}") from e
        raise MalloyError(f"Failed to load packages: {str(e)}") from e


async def load_models(
    client: MalloyAPIClient, project: Project, packages: list[Package]
) -> list[Model]:
    """Load models from the Malloy publisher.

    Args:
        client: The Malloy API client
        project: The project to load models from
        packages: List of packages to load models from

    Returns:
        list[Model]: List of models

    Raises:
        MalloyError: If no valid models are found
    """
    models: list[Model] = []
    for package in packages:
        try:
            package_models = client.list_models(project.name, package.name)
            for model in package_models:
                try:
                    model_details = client.get_model(project.name, package.name, model.path)
                    models.append(model_details)
                except Exception as e:
                    logging.warning(
                        "Failed to load model %s from package %s: %s",
                        model.path,
                        package.name,
                        str(e),
                    )
        except Exception as e:
            logging.warning(
                "Failed to load models from package %s: %s",
                package.name,
                str(e),
            )

    if not models:
        available_packages = ", ".join(p.name for p in packages)
        raise MalloyError(
            "No valid models found in any package. "
            f"Available packages: {available_packages}"
        )

    logging.info(f"Loaded {len(models)} models from {len(packages)} packages")
    return models


# Register resources using decorators
@mcp.resource("packages://{project_name}")
def get_packages(project_name: str) -> str:
    """Get packages for a project.

    Args:
        project_name: Name of the project

    Returns:
        str: JSON string containing package information
    """
    client = MalloyAPIClient("http://localhost:4000")
    try:
        packages = client.list_packages(project_name)
        return json.dumps([{
            "name": pkg.name,
            "description": pkg.description or ""
        } for pkg in packages], indent=2)
    finally:
        client.close()


@mcp.resource("models://{project_name}/{package_name}")
def get_models(project_name: str, package_name: str) -> str:
    """Get models for a package.

    Args:
        project_name: Name of the project
        package_name: Name of the package

    Returns:
        str: JSON string containing model information
    """
    client = MalloyAPIClient("http://localhost:4000")
    try:
        models = client.list_models(project_name, package_name)
        return json.dumps([{
            "name": model.path,
            "type": model.type,
            "package_name": model.package_name
        } for model in models], indent=2)
    finally:
        client.close()


@mcp.resource("model://{project_name}/{package_name}/{model_path}")
def get_model(project_name: str, package_name: str, model_path: str) -> str:
    """Get details for a specific model.

    Args:
        project_name: Name of the project
        package_name: Name of the package
        model_path: Path to the model

    Returns:
        str: JSON string containing model details
    """
    client = MalloyAPIClient("http://localhost:4000")
    try:
        # Cast the result to CompiledModel since get_model returns a compiled model
        model = cast(CompiledModel, client.get_model(project_name, package_name, model_path))
        return json.dumps({
            "name": model.path,
            "type": model.type,
            "package_name": model.package_name,
            "malloy_version": model.malloy_version,
            "data_styles": model.data_styles,
            "model_def": model.model_def,
            "sources": [source.model_dump() for source in model.sources],
            "queries": [query.model_dump() for query in model.queries],
            "notebook_cells": [cell.model_dump() for cell in model.notebook_cells]
        }, indent=2)
    finally:
        client.close()


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Manage application lifecycle and initialize resources.

    Args:
        server: The FastMCP server instance

    Yields:
        Application context for tools and resources

    Raises:
        MalloyError: If initialization fails
    """
    client = None
    try:
        # Connect to Malloy publisher
        client = connect_to_publisher("http://localhost:4000")

        # Get first project
        projects = client.list_projects()
        if not projects:
            raise MalloyError("No projects found")

        # Get packages for the first project
        try:
            packages = client.list_packages(projects[0].name)
            if not packages:
                raise MalloyError("No packages found")
        except Exception as e:
            raise MalloyError(f"Failed to list packages: {str(e)}") from e

        # Get models for each package
        models = []
        for package in packages:
            try:
                package_models = client.list_models(projects[0].name, package.name)
                models.extend(package_models)
            except Exception as e:
                logger.warning(f"Failed to list models for package {package.name}: {str(e)}")

        if not models:
            raise MalloyError("No valid models found")

        # Create minimal context for tools
        yield {
            "client": client,
            "project_name": projects[0].name,
        }

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


# Set lifespan after resource registration
mcp.settings.lifespan = app_lifespan

# Export the FastMCP instance
__all__ = ["mcp"]
