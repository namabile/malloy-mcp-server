"""
Malloy MCP Server - a streamlined MCP server for Malloy queries.

This package provides a Model Context Protocol (MCP) server for executing Malloy queries
and interacting with Malloy models. It connects to a running Malloy Publisher API
to provide query execution capabilities.

## Quick Start

1. Start the Malloy Publisher API on localhost:4000

2. Run the MCP server:
   ```bash
   malloy-mcp-server
   ```

3. Connect an MCP client like Claude Desktop and configure it to use this server.

## Usage Examples

```python
# Basic query execution
result = await execute_malloy_query(
    project_name="home",
    package_name="example",
    model_path="model.malloy",
    query="query: users -> { aggregate: count() }"
)

# Using a named query
result = await execute_malloy_query(
    project_name="home",
    package_name="example",
    model_path="model.malloy",
    source_name="users",
    query_name="user_stats"
)

# Listing available projects
projects = await list_projects()

# Listing packages in a project
packages = await list_packages(project_name="home")

# Listing models in a package
models = await list_models(
    project_name="home",
    package_name="example"
)

# Getting details about a specific model
model = await get_model(
    project_name="home",
    package_name="example",
    model_path="model.malloy"
)
```

## Common Errors and Troubleshooting

- **CONNECTION_ERROR**: Cannot connect to the Malloy Publisher API
  - Ensure the Malloy Publisher is running at http://localhost:4000/api/v0
  - Check if MALLOY_PUBLISHER_URL environment variable is set correctly

- **QUERY_EXECUTION_ERROR**: Error while executing a query
  - Check query syntax and ensure the model path is correct
  - Verify that the specified source name exists in the model

- **Missing Source Name**: When using query_name, source_name is required
  - Always specify both source_name and query_name when using named queries

- **Query Conflict**: Cannot provide both query and query_name
  - Use either direct query syntax or a named query, not both

For more information, see the documentation at:
https://github.com/namabile/malloy-mcp-server
"""

import logging
import sys

__version__ = "0.1.1"

from malloy_mcp_server.server import (
    create_malloy_query,
    execute_malloy_query,
    get_model,
    list_models,
    list_packages,
    list_projects,
    mcp,
)

# Configure logging
logger = logging.getLogger(__name__)


def main() -> None:
    """Run the MCP server.

    This function starts the Malloy MCP server using the stdio transport.
    The server connects to the Malloy Publisher API running at
    http://localhost:4000/api/v0 by default, or at the URL specified
    in the MALLOY_PUBLISHER_URL environment variable.

    Make sure the Malloy Publisher API is running before starting the server.
    """
    # Configure stderr logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    # Log startup information
    logger.info("Starting Malloy MCP Server...")
    logger.info("Connecting to Malloy Publisher API...")

    # Run the MCP server with stdio transport
    mcp.run(transport="stdio")


__all__ = [
    "create_malloy_query",
    "execute_malloy_query",
    "get_model",
    "list_models",
    "list_packages",
    "list_projects",
    "mcp",
]
