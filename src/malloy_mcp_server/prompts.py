"""Prompts for the Malloy MCP Server."""

from mcp.types import PromptMessage, TextContent

from .server import mcp


@mcp.prompt()
def create_malloy_query() -> list[PromptMessage]:
    """Create a basic prompt to help write Malloy queries."""
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
      group_by: status
      aggregate: order_count, total_revenue
    }
    """

    prompt_intro = (
        "You are creating a Malloy query. Use the examples below as guidance."
    )

    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text", text=f"{prompt_intro}\n\n{malloy_examples}"
            ),
        )
    ]
