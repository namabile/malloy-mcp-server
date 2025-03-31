"""Tests for the query executor."""

from typing import Any
from unittest.mock import MagicMock

import pytest

from malloy_mcp_server.errors import MalloyError
from malloy_mcp_server.tools import execute_malloy_query


@pytest.fixture
def mock_query_result() -> dict[str, Any]:
    """Create a mock query result."""
    return {
        "data_styles": {"style": "test"},
        "model_def": {"def": "test"},
        "query_result": [{"test": "data"}],
    }


@pytest.mark.asyncio
async def test_successful_query_execution(
    mock_client: MagicMock,
    mock_context: dict[str, Any],
    mock_query_result: dict[str, Any],
) -> None:
    """Test successful query execution."""
    # Configure mock response
    mock_client.execute_query.return_value = mock_query_result

    # Create tool call mock
    tool_call = MagicMock()
    tool_call.context = mock_context
    tool_call.parameters = {"query": "test_query"}

    # Execute query
    result = await execute_malloy_query(tool_call)

    # Verify result
    assert result is not None
    mock_client.execute_query.assert_called_once_with("test_query")


@pytest.mark.asyncio
async def test_query_execution_error(
    mock_client: MagicMock,
    mock_context: dict[str, Any],
) -> None:
    """Test handling of query execution errors."""
    # Configure error response
    mock_client.execute_query.side_effect = Exception("Query failed")

    # Create tool call mock
    tool_call = MagicMock()
    tool_call.context = mock_context
    tool_call.parameters = {"query": "test_query"}

    # Execute query and verify error
    with pytest.raises(MalloyError) as exc_info:
        await execute_malloy_query(tool_call)

    assert "Failed to execute query: Query failed" in str(exc_info.value)
