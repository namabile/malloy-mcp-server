# Malloy MCP Server

An MCP server implementation for executing Malloy queries and managing Malloy resources.

## Features

- Execute Malloy queries via MCP
- Access Malloy project, package, and model metadata
- Robust error handling with detailed context
- Comprehensive test coverage
- Type-safe implementation

## Installation

```bash
# Install using uv (recommended)
uv pip install malloy-mcp-server

# Or using pip
pip install malloy-mcp-server
```

## Usage

### Starting the Server

```python
from malloy_mcp_server import mcp

# Run the server
if __name__ == "__main__":
    mcp.serve()
```

### Configuration

The server can be configured using environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `MALLOY_PUBLISHER_ROOT_URL` | URL of the Malloy Publisher API | `http://localhost:4000` |

Example:
```bash
# Set the publisher URL
export MALLOY_PUBLISHER_ROOT_URL="http://malloy-publisher:4000"

# Run with custom configuration
python -m malloy_mcp_server
```

### Executing Queries

The server provides an MCP tool for executing Malloy queries:

```python
from malloy_mcp_server import ExecuteMalloyQueryTool

# Example query execution
result = await ExecuteMalloyQueryTool(
    query="select * from users",
    model_path="my_package/users"
)
```

### Accessing Resources

The server provides the following resource endpoints:

- `malloy://project/home/metadata` - Project metadata
- `malloy://project/home/package/{package_name}` - Package metadata
- `malloy://project/home/model/{model_path}` - Model metadata

## Development

### Setup

1. Clone the repository:
```bash
git clone https://github.com/namabile/malloy-mcp-server.git
cd malloy-mcp-server
```

2. Install dependencies:
```bash
uv pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=malloy_mcp_server
```

### Code Quality

The project uses:
- `black` for code formatting
- `mypy` for type checking
- `ruff` for linting

Run quality checks:
```bash
black .
mypy .
ruff check .
```

## Error Handling

The server provides detailed error handling with context:

```python
from malloy_mcp_server.errors import QueryExecutionError

try:
    result = await ExecuteMalloyQueryTool(...)
except QueryExecutionError as e:
    print(f"Error: {e.message}")
    print("Context:", e.context)
```

## Architecture

The server is built on:
- FastMCP for the MCP server implementation
- Malloy Publisher Client for Malloy interactions
- Pydantic for data validation

Key components:
- `server.py` - Core server implementation
- `tools/query_executor.py` - Query execution tool
- `errors.py` - Error handling utilities

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

MIT License - see LICENSE file for details 