"""Tests for the query executor."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from mcp.server.fastmcp import Context

from malloy_mcp_server.errors import MalloyError
from malloy_mcp_server.server import execute_malloy_query


@pytest.fixture
def mock_query_result() -> dict[str, Any]:
    """Create a mock query result."""
    return {
        "data_styles": {"style": "test"},
        "model_def": {"def": "test"},
        "query_result": [{"test": "data"}],
    }


@pytest.fixture
def mock_ctx(mock_context: dict[str, Any]) -> Context:
    """Create a mock Context object."""
    ctx = MagicMock(spec=Context)
    ctx.request_context = MagicMock()
    ctx.request_context.lifespan_context = mock_context
    return ctx


@pytest.mark.asyncio
async def test_successful_query_execution(
    mock_client: MagicMock,
    mock_context: dict[str, Any],
    mock_query_result: dict[str, Any],
    mock_ctx: Context,
) -> None:
    """Test successful query execution."""
    # Configure mock response
    mock_client.execute_query.return_value = mock_query_result

    # Execute query with new function signature
    result = await execute_malloy_query("test_query", mock_ctx)

    # Verify result
    assert result is not None
    mock_client.execute_query.assert_called_once_with("test_query")


@pytest.mark.asyncio
async def test_query_execution_error(
    mock_client: MagicMock,
    mock_context: dict[str, Any],
    mock_ctx: Context,
) -> None:
    """Test handling of query execution errors."""
    # Configure error response
    mock_client.execute_query.side_effect = Exception("Query failed")

    # Execute query and verify error
    with pytest.raises(MalloyError) as exc_info:
        await execute_malloy_query("test_query", mock_ctx)

    assert "Failed to execute query: Query failed" in str(exc_info.value)
