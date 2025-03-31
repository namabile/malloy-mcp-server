"""
Main entry point for the Malloy MCP Server.
"""

import asyncio
import logging
import sys

from uvicorn import Config, Server

from . import __version__, mcp

# Configure basic logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


async def main() -> None:
    """Start the Malloy MCP Server."""
    logger.info(f"Starting Malloy MCP Server v{__version__}")

    config = Config(app=mcp.sse_app(), host="127.0.0.1", port=3000, log_level="info")
    server = Server(config)

    try:
        await server.serve()
    except Exception as e:
        logger.error(f"Server failed to start: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
