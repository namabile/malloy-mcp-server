"""Tests for the Malloy MCP Server."""

from unittest.mock import AsyncMock, patch

import pytest

from malloy_mcp_server.errors import MalloyError
from malloy_mcp_server.server import app_lifespan, mcp


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.MalloyAPIClient")
async def test_app_lifespan_success(
    mock_api_client,
    mock_client,
    mock_project,
    mock_package,
    mock_model,
) -> None:
    """Test successful server initialization."""
    # Setup mock API client instance
    mock_api_instance = AsyncMock()
    mock_api_client.return_value = mock_api_instance
    
    # Configure mock responses
    mock_api_instance.list_projects = AsyncMock(return_value=[mock_project])
    mock_api_instance.list_packages = AsyncMock(return_value=[mock_package])
    mock_api_instance.list_models = AsyncMock(return_value=[mock_model])
    mock_api_instance.get_model = AsyncMock(return_value=mock_model)
    
    async with app_lifespan(mcp) as context:
        # Verify context is properly initialized
        assert context["client"] is not None
        assert context["project_name"] == mock_project.name


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.MalloyAPIClient")
async def test_app_lifespan_connection_error(mock_api_client, mock_client) -> None:
    """Test handling of connection errors."""
    # Setup mock API client instance
    mock_api_instance = AsyncMock()
    mock_api_client.return_value = mock_api_instance
    
    # Configure error response
    mock_api_instance.list_projects = AsyncMock(side_effect=Exception("Connection failed"))

    with pytest.raises(MalloyError) as exc_info:
        async with app_lifespan(mcp):
            pass

    assert "Failed to connect to Malloy publisher" in str(exc_info.value)
    assert exc_info.value.context["attempts"] == 3


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.MalloyAPIClient")
async def test_app_lifespan_no_projects(mock_api_client, mock_client) -> None:
    """Test handling of empty projects list."""
    # Setup mock API client instance
    mock_api_instance = AsyncMock()
    mock_api_client.return_value = mock_api_instance
    
    # Configure empty response
    mock_api_instance.list_projects = AsyncMock(return_value=[])

    with pytest.raises(MalloyError) as exc_info:
        async with app_lifespan(mcp):
            pass

    assert "Failed to connect to Malloy publisher" in str(exc_info.value)


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.MalloyAPIClient")
async def test_app_lifespan_package_error(
    mock_api_client,
    mock_client,
    mock_project,
) -> None:
    """Test handling of package listing errors."""
    # Setup mock API client instance
    mock_api_instance = AsyncMock()
    mock_api_client.return_value = mock_api_instance
    
    # Configure responses
    mock_api_instance.list_projects = AsyncMock(return_value=[mock_project])
    mock_api_instance.list_packages = AsyncMock(side_effect=Exception("Failed to list packages"))

    with pytest.raises(MalloyError) as exc_info:
        async with app_lifespan(mcp):
            pass

    assert "Failed to list packages" in str(exc_info.value)
    assert exc_info.value.context["project"] == mock_project.name


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.MalloyAPIClient")
async def test_app_lifespan_no_models(
    mock_api_client,
    mock_client,
    mock_project,
    mock_package,
) -> None:
    """Test handling of empty models list."""
    # Setup mock API client instance
    mock_api_instance = AsyncMock()
    mock_api_client.return_value = mock_api_instance
    
    # Configure responses
    mock_api_instance.list_projects = AsyncMock(return_value=[mock_project])
    mock_api_instance.list_packages = AsyncMock(return_value=[mock_package])
    mock_api_instance.list_models = AsyncMock(return_value=[])

    with pytest.raises(MalloyError) as exc_info:
        async with app_lifespan(mcp):
            pass

    assert "No valid models found" in str(exc_info.value)
    assert exc_info.value.context["project"] == mock_project.name
    assert mock_package.name in str(exc_info.value.context["packages"])
