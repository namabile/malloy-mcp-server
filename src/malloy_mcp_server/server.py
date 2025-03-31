"""MCP server for executing Malloy queries."""

import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, suppress
from typing import Any, cast

from malloy_publisher_client import (
    MalloyAPIClient,
    Model,
    Package,
    Project,
)
from malloy_publisher_client.api_client import APIError
from malloy_publisher_client.models import CompiledModel
from mcp.server.fastmcp import FastMCP

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
        error_msg = (
            f"Failed to connect to Malloy Publisher: {e.message}"
            if isinstance(e, APIError)
            else f"Failed to connect to Malloy Publisher: {e!s}"
        )
        raise MalloyError(error_msg) from e


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
        error_msg = (
            f"Failed to load packages: {e.message}"
            if isinstance(e, APIError)
            else f"Failed to load packages: {e!s}"
        )
        raise MalloyError(error_msg) from e


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
                    model_details = client.get_model(
                        project.name, package.name, model.path
                    )
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
        error_msg = (
            "No valid models found in any package. "
            f"Available packages: {available_packages}"
        )
        raise MalloyError(error_msg)

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
        return json.dumps(
            [
                {"name": pkg.name, "description": pkg.description or ""}
                for pkg in packages
            ]
        )
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
        return json.dumps(
            [
                {
                    "name": model.path,
                    "type": model.type,
                    "package_name": model.package_name,
                }
                for model in models
            ]
        )
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
        model = cast(
            CompiledModel, client.get_model(project_name, package_name, model_path)
        )
        return json.dumps(
            {
                "name": model.path,
                "type": model.type,
                "package_name": model.package_name,
                "malloy_version": model.malloy_version,
                "data_styles": model.data_styles,
                "model_def": model.model_def,
                "sources": [source.model_dump() for source in model.sources],
                "queries": [query.model_dump() for query in model.queries],
                "notebook_cells": [cell.model_dump() for cell in model.notebook_cells],
            }
        )
    finally:
        client.close()


@asynccontextmanager
async def app_lifespan(_: FastMCP) -> AsyncIterator[dict[str, Any]]:
    """Manage application lifecycle and initialize resources.

    Args:
        _: The FastMCP server instance (unused)

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
            error_msg = "No projects found"
            raise MalloyError(error_msg)

        # Get packages for the first project
        try:
            packages = client.list_packages(projects[0].name)
            if not packages:
                error_msg = "No packages found"
                raise MalloyError(error_msg)
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
            error_msg = "No valid models found"
            raise MalloyError(error_msg)

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


# Set lifespan
mcp.settings.lifespan = app_lifespan

# Export the FastMCP instance
__all__ = ["mcp"]
