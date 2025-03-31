"""Tests for the query executor."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from malloy_publisher_client import QueryParams

from malloy_mcp_server.errors import MalloyError
from malloy_mcp_server.server import connect_to_publisher, execute_malloy_query


@pytest.fixture
def mock_query_result() -> dict[str, Any]:
    """Create a mock query result."""
    return {
        "data_styles": {"style": "test"},
        "model_def": {"def": "test"},
        "query_result": [{"test": "data"}],
    }


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.connect_to_publisher")
async def test_successful_query_execution(
    mock_connect_to_publisher: MagicMock,
    mock_client: MagicMock,
    mock_query_result: dict[str, Any],
) -> None:
    """Test successful query execution."""
    # Configure mock response
    mock_connect_to_publisher.return_value = mock_client
    mock_client.execute_query.return_value = mock_query_result

    # Execute query with new function signature
    result = await execute_malloy_query(
        project_name="test_project",
        package_name="test_package",
        model_path="test_model.malloy",
        query="test_query",
    )

    # Verify result
    assert result is not None
    mock_client.execute_query.assert_called_once_with(
        QueryParams(
            project_name="test_project",
            package_name="test_package",
            path="test_model.malloy",
            query="test_query",
        )
    )


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.connect_to_publisher")
async def test_query_execution_with_query_name(
    mock_connect_to_publisher: MagicMock,
    mock_client: MagicMock,
    mock_query_result: dict[str, Any],
) -> None:
    """Test successful query execution with query name."""
    # Configure mock response
    mock_connect_to_publisher.return_value = mock_client
    mock_client.execute_query.return_value = mock_query_result

    # Execute query with new function signature using query_name
    result = await execute_malloy_query(
        project_name="test_project",
        package_name="test_package",
        model_path="test_model.malloy",
        source_name="test_source",
        query_name="test_named_query",
    )

    # Verify result
    assert result is not None
    mock_client.execute_query.assert_called_once_with(
        QueryParams(
            project_name="test_project",
            package_name="test_package",
            path="test_model.malloy",
            source_name="test_source",
            query_name="test_named_query",
        )
    )


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.connect_to_publisher")
async def test_model_path_only_execution(
    mock_connect_to_publisher: MagicMock,
    mock_client: MagicMock,
    mock_query_result: dict[str, Any],
) -> None:
    """Test successful execution with only model path provided."""
    # Configure mock response
    mock_connect_to_publisher.return_value = mock_client
    mock_client.execute_query.return_value = mock_query_result

    # Execute query with only model path
    result = await execute_malloy_query(
        project_name="test_project",
        package_name="test_package",
        model_path="test_model.malloy",
    )

    # Verify result
    assert result is not None
    mock_client.execute_query.assert_called_once_with(
        QueryParams(
            project_name="test_project",
            package_name="test_package",
            path="test_model.malloy",
        )
    )


@pytest.mark.asyncio
@patch("malloy_mcp_server.server.connect_to_publisher")
async def test_query_execution_error(
    mock_connect_to_publisher: MagicMock,
    mock_client: MagicMock,
) -> None:
    """Test handling of query execution errors."""
    # Configure error response
    mock_connect_to_publisher.return_value = mock_client
    mock_client.execute_query.side_effect = Exception("Query failed")

    # Execute query and verify error
    with pytest.raises(MalloyError) as exc_info:
        await execute_malloy_query(
            project_name="test_project",
            package_name="test_package",
            model_path="test_model.malloy",
            query="test_query",
        )

    assert "Failed to execute query: Query failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_query_execution_validation_error_query_conflict() -> None:
    """Test validation error when both query and query_name are provided."""
    with pytest.raises(MalloyError) as exc_info:
        await execute_malloy_query(
            project_name="test_project",
            package_name="test_package",
            model_path="test_model.malloy",
            query="test_query",
            query_name="test_named_query",
        )

    assert "Parameters 'query' and 'query_name' are mutually exclusive" in str(
        exc_info.value
    )


@pytest.mark.asyncio
async def test_query_execution_validation_error_missing_source_name() -> None:
    """Test validation error when query_name is provided without source_name."""
    with pytest.raises(MalloyError) as exc_info:
        await execute_malloy_query(
            project_name="test_project",
            package_name="test_package",
            model_path="test_model.malloy",
            query_name="test_named_query",
        )

    assert "Parameter 'source_name' is required when using 'query_name'" in str(
        exc_info.value
    )
