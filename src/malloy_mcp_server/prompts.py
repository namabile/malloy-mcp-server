"""Prompt generation for Malloy queries."""

from mcp.types import TextContent

from malloy_mcp_server.server import mcp


@mcp.prompt("malloy")
def create_malloy_query(message: str) -> TextContent:
    """Create a Malloy query from a natural language prompt."""
    malloy_examples = """
    # Basic Malloy query examples:
    # Example 1: Simple aggregation
    source: orders is table('orders.parquet') extend {
      measure: order_count is count()
      measure: total_revenue is sum(amount)
    }
    query: orders -> {
      aggregate: order_count, total_revenue
    }
    # Example 2: Group by with aggregation
    query: orders -> {
      group_by: category
      aggregate: order_count, total_revenue
    }
    """
    return TextContent(
        type="text",
        text=f"Based on these Malloy examples:\n{malloy_examples}\n"
        f"Create a Malloy query for: {message}",
    )


# Export prompts
__all__ = ["create_malloy_query"]
