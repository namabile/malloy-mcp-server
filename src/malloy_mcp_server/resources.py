"""Resource registration for the Malloy MCP Server."""

from typing import Any, Dict, List

from malloy_publisher_client import Model, Package, Project
from mcp.server.fastmcp import FastMCP


def register_resources(
    server: FastMCP, project: Project, packages: List[Package], models: List[Model]
) -> None:
    """Register all Malloy resources with the MCP server.

    Args:
        server: The FastMCP server instance
        project: The Malloy project
        packages: List of Malloy packages
        models: List of Malloy models
    """

    # Register project metadata
    @server.resource("malloy://project/home/metadata")
    def get_project_metadata() -> Dict[str, Any]:
        """Get metadata about the Malloy project and its contents."""
        return {
            **project.model_dump(),
            "packages": [pkg.model_dump() for pkg in packages],
            "models": [model.model_dump() for model in models],
        }

    # Register package resources
    for pkg in packages:
        register_package(server, pkg)

    # Register model resources
    for model in models:
        register_model(server, model)

    # Health check resource
    @server.resource("malloy://healthcheck")
    def get_healthcheck() -> Dict[str, Any]:
        """Get server health status."""
        return {
            "status": "healthy",
            "version": "0.1.0",
        }


def register_package(server: FastMCP, package: Package) -> None:
    """Register a resource for a specific package.

    Args:
        server: The FastMCP server instance
        package: The Malloy package
    """
    resource_path = f"malloy://project/home/package/{package.name}"

    @server.resource(resource_path)
    def get_package() -> Dict[str, Any]:
        """Get metadata for a specific package."""
        return package.model_dump()


def register_model(server: FastMCP, model: Model) -> None:
    """Register a resource for a specific model.

    Args:
        server: The FastMCP server instance
        model: The Malloy model
    """
    resource_path = f"malloy://project/home/model/{model.path}"

    @server.resource(resource_path)
    def get_model() -> Dict[str, Any]:
        """Get metadata for a specific model."""
        return model.model_dump()
