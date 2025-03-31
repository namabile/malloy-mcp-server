"""Test fixtures for the Malloy MCP Server."""

from typing import Any, AsyncGenerator, Dict
from unittest.mock import AsyncMock, MagicMock

import pytest
from malloy_publisher_client import MalloyAPIClient, Model, Package, Project
from mcp.server.fastmcp import Context

from malloy_mcp_server import mcp


@pytest.fixture
def mock_project() -> Project:
    """Create a mock Malloy project."""
    return Project(name="test_project")


@pytest.fixture
def mock_package() -> Package:
    """Create a mock Malloy package."""
    return Package(
        name="test_package", 
        description="Test package description"
    )


@pytest.fixture
def mock_model() -> Model:
    """Create a mock Malloy model."""
    return Model(
        path="test_package/test_model",
        type="source",
        packageName="test_package"
    )


@pytest.fixture
def mock_client(
    mock_project: Project,
    mock_package: Package,
    mock_model: Model,
) -> AsyncMock:
    """Create a mock MalloyAPIClient."""
    client = AsyncMock(spec=MalloyAPIClient)

    # Configure mock responses
    client.list_projects.return_value = [mock_project]
    client.list_packages.return_value = [mock_package]
    client.list_models.return_value = [mock_model]
    client.get_model.return_value = mock_model
    client.execute_query.return_value = MagicMock(
        data_styles='{"style": "test"}',
        model_def='{"def": "test"}',
        query_result='[{"test": "data"}]',
    )

    return client


@pytest.fixture
def mock_context() -> Context:
    """Create a mock MCP Context."""
    context = MagicMock(spec=Context)
    context.info = AsyncMock()
    context.error = AsyncMock()
    context.report_progress = AsyncMock()
    return context


@pytest.fixture
async def app_context(
    mock_client: AsyncMock,
    mock_project: Project,
    mock_package: Package,
    mock_model: Model,
) -> AsyncGenerator[Dict[str, Any], None]:
    """Create a mock application context."""
    ctx = MagicMock()
    ctx.client = mock_client
    ctx.project = mock_project
    ctx.packages = [mock_package]
    ctx.models = [mock_model]
    yield ctx
