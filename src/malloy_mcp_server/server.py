"""
Malloy MCP Server implementation using the official MCP Python SDK.
Provides tools and prompts for interacting with Malloy data models.
"""

from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager, suppress
from typing import Any, cast
import asyncio

from malloy_publisher_client import (
    MalloyAPIClient,
    QueryParams,
    Model,
    Package,
    Project,
    CompiledModel,
)
from mcp.server.fastmcp import FastMCP, Context
from pydantic import BaseModel


class AppContext(BaseModel):
    """Application context available during request processing."""

    model_config = {"arbitrary_types_allowed": True}

    client: MalloyAPIClient
    project: Project
    packages: list[Package]
    models: list[CompiledModel]


MetadataGetter = Callable[[], dict[str, Any]]


def create_package_metadata_getter(pkg: Package) -> MetadataGetter:
    """Create a closure for getting package metadata."""
    def get_package_metadata() -> dict[str, Any]:
        """Get metadata for a Malloy package."""
        return pkg.model_dump()
    return get_package_metadata


def create_model_metadata_getter(model: CompiledModel) -> MetadataGetter:
    """Create a closure for getting model metadata."""
    def get_model_metadata() -> dict[str, Any]:
        """Get metadata for a Malloy model."""
        return model.model_dump()
    return get_model_metadata


@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle and initialize resources."""
    client: MalloyAPIClient | None = None
    try:
        # Initialize Malloy publisher client with retry logic
        for attempt in range(3):  # Try 3 times
            try:
                client = MalloyAPIClient("http://localhost:4000")
                # Test the connection
                projects = await client.list_projects()  # type: ignore[misc]
                if not projects:
                    raise RuntimeError("No projects found in Malloy publisher")
                break  # Connection successful
            except Exception as e:
                if attempt == 2:  # Last attempt
                    raise RuntimeError(f"Failed to connect to Malloy publisher after 3 attempts: {str(e)}")
                if client:
                    client.close()
                    client = None
                await asyncio.sleep(1)  # Wait before retrying

        # At this point, client must be initialized successfully
        client = cast(MalloyAPIClient, client)
        project = projects[0]  # Use first project
        packages = []
        models = []

        # Get packages in the project
        packages = await client.list_packages(project_name=project.name)  # type: ignore[misc]
        
        for pkg in packages:
            try:
                # Get models in the package
                pkg_models = await client.list_models(  # type: ignore[misc]
                    project_name=project.name,
                    package_name=pkg.name
                )
                
                # Process all models for this package
                for model in pkg_models:
                    try:
                        model_details = await client.get_model(  # type: ignore[misc]
                            project_name=project.name,
                            package_name=pkg.name,
                            model_name=model.path
                        )
                        models.append(model_details)
                    except Exception as e:
                        print(f"Warning: Failed to process model {model.path}: {str(e)}")
                        continue

            except Exception as e:
                print(f"Warning: Failed to process package {pkg.name}: {str(e)}")
                continue

        # Create resource getters
        @server.resource("malloy://project/home/metadata")
        def get_project_metadata() -> dict[str, Any]:
            """Get metadata about the Malloy project and its contents."""
            return {
                "name": project.name,
                "packages": [pkg.model_dump() for pkg in packages],
                "models": [model.model_dump() for model in models]
            }

        for pkg in packages:
            getter = create_package_metadata_getter(pkg)
            server.resource(f"malloy://project/home/package/{pkg.name}")(getter)

        for model in models:
            getter = create_model_metadata_getter(model)
            server.resource(f"malloy://project/home/model/{model.path}")(getter)

        # Create and yield the context
        context = AppContext(
            client=client,
            project=project,
            packages=packages,
            models=models
        )
        yield context

    except Exception as e:
        error_msg = f"Failed to initialize Malloy resources: {str(e)}"
        print(error_msg)
        if client:
            client.close()
        raise RuntimeError(error_msg) from e

    finally:
        if client:
            with suppress(Exception):
                client.close()


# Initialize MCP server with proper capabilities and lifespan
mcp = FastMCP(
    name="malloy-mcp-server",
    description="MCP server for Malloy data analysis and query execution",
    capabilities={
        "prompts": {"listChanged": True},
        "resources": {"subscribelistChanged": True},
        "tools": {"listChanged": True},
        "logging": True,
        "completion": True,
    },
    lifespan=app_lifespan,
)

# Export the FastMCP instance
__all__ = ["mcp"]
