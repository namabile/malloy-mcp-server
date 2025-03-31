"""Tests for the Malloy MCP Server."""

import os
from unittest.mock import MagicMock, patch

import pytest
from malloy_publisher_client import Model, Package, Project
from malloy_publisher_client.models import ModelType

from malloy_mcp_server.errors import MalloyError
from malloy_mcp_server.server import app_lifespan, connect_to_publisher, mcp


@pytest.fixture
def mock_project() -> Project:
    """Create a mock project."""
    return Project(name="test_project")


@pytest.fixture
def mock_package() -> Package:
    """Create a mock package."""
    return Package(name="test_package", description="Test package description")


@pytest.fixture
def mock_model() -> Model:
    """Create a mock model."""
    return Model(
        packageName="test_package", path="test_model.malloynb", type=ModelType.NOTEBOOK
    )


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.MalloyAPIClient")
async def test_app_lifespan_success(
    mock_api_client: MagicMock,
    mock_project: Project,
    mock_package: Package,
    mock_model: Model,
) -> None:
    """Test successful server initialization."""
    # Setup mock API client instance
    mock_api_instance = MagicMock()
    mock_api_client.return_value = mock_api_instance

    # Configure mock responses
    mock_api_instance.list_projects.return_value = [mock_project]
    mock_api_instance.list_packages.return_value = [mock_package]
    mock_api_instance.list_models.return_value = [mock_model]
    mock_api_instance.get_model.return_value = mock_model

    async with app_lifespan(mcp) as context:
        # Verify context is properly initialized
        assert context["client"] is not None
        assert context["project_name"] == mock_project.name


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.MalloyAPIClient")
async def test_app_lifespan_connection_error(
    mock_api_client: MagicMock,
) -> None:
    """Test handling of connection errors."""
    # Setup mock API client instance
    mock_api_instance = MagicMock()
    mock_api_client.return_value = mock_api_instance

    # Configure error response
    mock_api_instance.list_projects.side_effect = Exception("Connection failed")

    with pytest.raises(MalloyError) as exc_info:
        async with app_lifespan(mcp):
            pass

    assert "Failed to connect to Malloy Publisher: Connection failed" in str(
        exc_info.value
    )


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.MalloyAPIClient")
async def test_app_lifespan_no_projects(
    mock_api_client: MagicMock,
) -> None:
    """Test handling of empty projects list."""
    # Setup mock API client instance
    mock_api_instance = MagicMock()
    mock_api_client.return_value = mock_api_instance

    # Configure empty response
    mock_api_instance.list_projects.return_value = []

    with pytest.raises(MalloyError) as exc_info:
        async with app_lifespan(mcp):
            pass

    assert "No projects found" in str(exc_info.value)


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.MalloyAPIClient")
async def test_app_lifespan_package_error(
    mock_api_client: MagicMock,
    mock_project: Project,
) -> None:
    """Test handling of package listing errors."""
    # Setup mock API client instance
    mock_api_instance = MagicMock()
    mock_api_client.return_value = mock_api_instance

    # Configure responses
    mock_api_instance.list_projects.return_value = [mock_project]
    mock_api_instance.list_packages.side_effect = Exception("Failed to list packages")

    with pytest.raises(MalloyError) as exc_info:
        async with app_lifespan(mcp):
            pass

    assert "Failed to list packages" in str(exc_info.value)


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.MalloyAPIClient")
async def test_app_lifespan_no_models(
    mock_api_client: MagicMock,
    mock_project: Project,
    mock_package: Package,
) -> None:
    """Test handling of empty models list."""
    # Setup mock API client instance
    mock_api_instance = MagicMock()
    mock_api_client.return_value = mock_api_instance

    # Configure responses
    mock_api_instance.list_projects.return_value = [mock_project]
    mock_api_instance.list_packages.return_value = [mock_package]
    mock_api_instance.list_models.return_value = []

    with pytest.raises(MalloyError) as exc_info:
        async with app_lifespan(mcp):
            pass

    assert "No valid models found" in str(exc_info.value)


def test_publisher_url_from_env():
    """Test that the publisher URL can be set via environment variable."""
    # Store original value
    orig_url = os.environ.get("MALLOY_PUBLISHER_ROOT_URL")

    try:
        # Set environment variable
        test_url = "http://test-publisher:5000"
        os.environ["MALLOY_PUBLISHER_ROOT_URL"] = test_url

        # Mock the MalloyAPIClient to avoid actual connection attempts
        with patch("malloy_mcp_server.server.MalloyAPIClient") as mock_client_class:
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Call the function
            connect_to_publisher()

            # Verify URL was used
            mock_client_class.assert_called_once_with(test_url)

    finally:
        # Restore original environment
        if orig_url is not None:
            os.environ["MALLOY_PUBLISHER_ROOT_URL"] = orig_url
        else:
            del os.environ["MALLOY_PUBLISHER_ROOT_URL"]
