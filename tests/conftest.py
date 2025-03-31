"""Test fixtures for the Malloy MCP Server."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from malloy_publisher_client import Model, Package, Project
from malloy_publisher_client.models import ModelType
from starlette.applications import Starlette
from starlette.testclient import TestClient

from malloy_mcp_server.server import mcp


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


@pytest.fixture
def mock_client() -> MagicMock:
    """Create a mock API client."""
    return MagicMock()


@pytest.fixture
def mock_context(mock_client: MagicMock) -> dict[str, Any]:
    """Create a mock context."""
    return {"client": mock_client, "project_name": "test_project"}


@pytest.fixture
def app(_: dict[str, Any]) -> Starlette:
    """Create a Starlette app with mock context."""
    return mcp.sse_app()


@pytest.fixture
def test_client(app: Starlette) -> TestClient:
    """Create a test client for Starlette app."""
    return TestClient(app)
