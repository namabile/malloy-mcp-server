"""Tests for the Malloy query executor tool."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from malloy_mcp_server.errors import MalloyError
from malloy_mcp_server.tools import execute_malloy_query


class QueryInput(BaseModel):
    """Input parameters for query execution."""
    query: str
    model_path: str


@pytest.mark.asyncio
async def test_successful_query_execution(mock_context, app_context):
    """Test successful query execution."""
    # Setup mock client with AsyncMock for execute_query
    client_mock = AsyncMock()
    mock_result = MagicMock()
    mock_result.data_styles = '{"style": "test"}'
    mock_result.model_def = '{"def": "test"}'
    mock_result.query_result = '[{"test": "data"}]'
    
    # Set up the AsyncMock to return the mock result
    client_mock.execute_query.return_value = mock_result
    
    # Setup context
    mock_context.request_context.lifespan_context = {
        "client": client_mock,
        "project_name": app_context.project.name,
    }
    
    # Execute
    result = await execute_malloy_query(
        query="select * from test", 
        model_path="test_package/test_model",
        ctx=mock_context
    )

    # Verify
    assert isinstance(result, dict)
    assert result["data_styles"] == {"style": "test"}
    assert result["model_def"] == {"def": "test"}
    assert result["query_result"] == [{"test": "data"}]
    client_mock.execute_query.assert_called_once()


@pytest.mark.asyncio
async def test_query_execution_error(mock_context, app_context):
    """Test handling of query execution errors."""
    # Setup
    client_mock = AsyncMock()
    client_mock.execute_query.side_effect = Exception("Query failed")
    
    mock_context.request_context.lifespan_context = {
        "client": client_mock,
        "project_name": app_context.project.name,
    }

    # Execute and verify
    with pytest.raises(MalloyError) as exc_info:
        await execute_malloy_query(
            query="select * from test", 
            model_path="test_package/test_model",
            ctx=mock_context
        )
    assert "Query execution failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_json_parse_error(mock_context, app_context):
    """Test handling of JSON parsing errors."""
    # Setup
    client_mock = AsyncMock()
    mock_result = MagicMock()
    mock_result.data_styles = '{"style": "test"}'
    mock_result.model_def = '{"def": "test"}'
    mock_result.query_result = 'invalid json'
    client_mock.execute_query.return_value = mock_result
    
    mock_context.request_context.lifespan_context = {
        "client": client_mock,
        "project_name": app_context.project.name,
    }

    # Execute and verify
    with pytest.raises(MalloyError) as exc_info:
        await execute_malloy_query(
            query="select * from test", 
            model_path="test_package/test_model",
            ctx=mock_context
        )
    assert "Failed to parse query results" in str(exc_info.value)
