"""MCP server for executing Malloy queries."""

import asyncio
import logging
import random
from collections.abc import AsyncIterator, Awaitable
from contextlib import asynccontextmanager, suppress
from typing import Any, Dict, List, Tuple, cast

from malloy_publisher_client import (
    MalloyAPIClient,
    Model,
    Package,
    Project,
)
from mcp.server.fastmcp import FastMCP

from .errors import MalloyError, format_error
from .resources import register_resources

# Configure logging
logger = logging.getLogger(__name__)


async def connect_with_backoff(
    max_retries: int = 3, base_delay: float = 0.5
) -> Tuple[MalloyAPIClient, Project]:
    """Connect to the Malloy publisher with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay between retries in seconds

    Returns:
        A tuple containing the client and first project

    Raises:
        MalloyError: If connection fails after retries
    """
    client = None
    for retry in range(max_retries):
        try:
            client = MalloyAPIClient("http://localhost:4000")
            projects = cast(List[Project], await cast(Awaitable[Any], client.list_projects()))
            if projects:
                return client, projects[0]  # Use first project

            # Close client with proper error handling
            try:
                client.close()
            except Exception as close_error:
                logger.warning(f"Error closing client: {close_error}")
            
            client = None

            # Exponential backoff with jitter
            delay = base_delay * (2**retry) * (0.8 + 0.4 * random.random())
            await asyncio.sleep(delay)

        except Exception as e:
            if client:
                try:
                    client.close()
                except Exception as close_error:
                    logger.warning(f"Error closing client: {close_error}")
                client = None
            if retry == max_retries - 1:
                msg_part1 = "Failed to connect to Malloy publisher after "
                msg_part2 = f"{max_retries} attempts"
                error_msg = msg_part1 + msg_part2
                raise MalloyError(
                    error_msg,
                    {
                        "attempts": max_retries,
                        "url": "http://localhost:4000",
                        "error": str(e),
                    },
                ) from e

            # Exponential backoff with jitter
            delay = base_delay * (2**retry) * (0.8 + 0.4 * random.random())
            await asyncio.sleep(delay)

    raise MalloyError(
        "Failed to connect to Malloy publisher",
        {"attempts": max_retries, "url": "http://localhost:4000"},
    )


async def load_packages(client: MalloyAPIClient, project: Project) -> List[Package]:
    """Load packages for a project.

    Args:
        client: The Malloy API client
        project: The Malloy project

    Returns:
        List of packages

    Raises:
        MalloyError: If loading packages fails
    """
    try:
        packages = cast(
            List[Package], 
            await cast(Awaitable[Any], client.list_packages(project_name=project.name))
        )
        return packages
    except Exception as e:
        raise MalloyError(
            f"Failed to list packages: {str(e)}", 
            {"project": project.name}
        ) from e


async def load_models(
    client: MalloyAPIClient, project: Project, packages: List[Package]
) -> List[Model]:
    """Load models from all packages.

    Args:
        client: The Malloy API client
        project: The Malloy project
        packages: List of packages to load models from

    Returns:
        List of models

    Raises:
        MalloyError: If loading models fails
    """
    models: List[Model] = []

    for pkg in packages:
        try:
            pkg_models = cast(
                List[Model], 
                await cast(Awaitable[Any], client.list_models(
                    project_name=project.name, 
                    package_name=pkg.name
                ))
            )

            for model in pkg_models:
                try:
                    model_details = cast(
                        Model, 
                        await cast(Awaitable[Any], client.get_model(
                            project_name=project.name,
                            package_name=pkg.name,
                            model_name=model.path,
                        ))
                    )
                    models.append(model_details)
                except Exception as e:
                    logger.warning(f"Failed to load model {model.path}: {str(e)}")

        except Exception as e:
            logger.warning(f"Failed to process package {pkg.name}: {str(e)}")

    if not models:
        raise MalloyError(
            "No valid models found",
            {"project": project.name, "packages": [p.name for p in packages]}
        )

    return models


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
        client, project = await connect_with_backoff()

        # Load packages and models
        packages = await load_packages(client, project)
        models = await load_models(client, project, packages)

        # Register resources
        register_resources(server, project, packages, models)

        # Create minimal context for tools
        yield {
            "client": client,
            "project_name": project.name,
        }

    except Exception as e:
        error_msg = format_error(
            e if isinstance(e, MalloyError) else MalloyError(str(e))
        )
        logger.error(error_msg)
        if client:
            try:
                client.close()
            except Exception as close_error:
                logger.warning(f"Error closing client: {close_error}")
        raise

    finally:
        if client:
            with suppress(Exception):
                try:
                    client.close()
                except Exception as close_error:
                    logger.warning(f"Error closing client: {close_error}")


# Initialize MCP server with minimal capabilities
mcp = FastMCP(
    name="malloy-mcp-server",
    description="MCP server for Malloy queries",
    # Only declare capabilities actually used
    capabilities={
        "resources": {"subscribelistChanged": True},
        "tools": {"listChanged": True},
    },
    lifespan=app_lifespan,
)

# Export the FastMCP instance
__all__ = ["mcp"]
