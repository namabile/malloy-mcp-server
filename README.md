# Malloy MCP Server

A FastAPI-based MCP (Model Control Protocol) server that interfaces with the Malloy Publisher client.

## Setup

1. Create and activate a Python virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install fastapi uvicorn pydantic
```

3. Make sure the `malloy-publisher-client` directory is in the parent directory of this project.

## Running the Server

Start the server with:
```bash
python main.py
```

The server will run on `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs`.

## API Endpoints

### Health Check
- `GET /health`
  - Returns the server health status

### Query Execution
- `POST /query`
  - Execute a Malloy query
  - Request body:
    ```json
    {
      "query": "your malloy query",
      "connection_name": "optional connection name"
    }
    ```

### Connection Management
- `POST /connections`
  - Create a new connection
  - Request body:
    ```json
    {
      "name": "connection name",
      "config": {
        // connection configuration
      }
    }
    ```

- `GET /connections`
  - List all available connections

## Error Handling

The server provides detailed error messages when:
- The Malloy Publisher client fails to initialize
- Queries fail to execute
- Connection operations fail
- Invalid requests are made

All errors are returned with appropriate HTTP status codes and error messages. 