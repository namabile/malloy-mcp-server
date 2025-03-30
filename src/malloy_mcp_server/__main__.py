"""Main entry point for the Malloy MCP server."""

import asyncio

from .server import mcp


async def main() -> None:
    """Start and run the Malloy MCP server."""
    try:
        # Run the server indefinitely
        await mcp.serve()
    except KeyboardInterrupt:
        print("\nShutting down server...")
    finally:
        await mcp.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
