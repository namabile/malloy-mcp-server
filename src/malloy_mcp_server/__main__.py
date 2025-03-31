"""
Main entry point for the Malloy MCP Server.
"""

import sys
import logging
from malloy_mcp_server.server import mcp

if __name__ == "__main__":
    # Configure stderr logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )
    
    # Log startup information
    logger = logging.getLogger(__name__)
    logger.info("Starting Malloy MCP Server...")
    
    # Run the MCP server
    mcp.run()
