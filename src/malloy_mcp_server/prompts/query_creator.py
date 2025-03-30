"""Prompt for assisting in creating Malloy queries."""

from typing import Any

from mcp.server.fastmcp import Context

from ..server import mcp


@mcp.prompt()
async def create_malloy_query(
    model_path: str,
    requirements: str,
    available_sources: list[str],
    ctx: Context,
) -> dict[str, str]:
    """Create a Malloy query based on the available models and requirements.

    Args:
        model_path: Path to the Malloy model to query against
        requirements: Description of what data needs to be queried
        available_sources: List of available sources in the model
        ctx: The MCP context for progress reporting and error handling

    Returns:
        Dictionary containing the generated query and explanation

    Raises:
        ValueError: If query generation fails
    """
    try:
        # Build context for query generation
        context = _build_context(model_path, requirements, available_sources)

        # Generate the query
        query = _generate_query(context)

        return {
            "query": query,
            "explanation": _explain_query(query),
        }

    except Exception as e:
        error_msg = f"Failed to generate Malloy query: {str(e)}"
        error_context = {
            "model_path": model_path,
            "requirements": requirements,
            "available_sources": available_sources,
        }
        await ctx.error(f"{error_msg}\nContext: {error_context}")
        raise ValueError(error_msg) from None


def _build_context(
    model_path: str, requirements: str, sources: list[str]
) -> dict[str, Any]:
    """Build context for query generation."""
    return {
        "model_path": model_path,
        "requirements": requirements,
        "sources": sources,
        "best_practices": [
            "Use clear and descriptive names for dimensions and measures",
            "Leverage Malloy's nested queries for complex analysis",
            "Use appropriate aggregations based on data types",
            "Include relevant filters to focus the analysis",
            "Consider performance implications of joins and aggregations",
        ],
    }


def _generate_query(context: dict[str, Any]) -> str:
    """Generate a Malloy query based on context."""
    # This is a placeholder - in a real implementation, this would use
    # the Malloy documentation and best practices to generate a query
    # based on the requirements and available sources
    return f"""
    query: {context['sources'][0]} ->
    {{
        group_by: dimension1
        aggregate:
            measure1
    }}
    """


def _explain_query(query: str) -> str:
    """Generate an explanation of the query."""
    # This is a placeholder - in a real implementation, this would
    # provide a clear explanation of what the query does and why
    # certain choices were made
    return (
        "This query groups the data by dimension1 and calculates "
        "measure1 for each group."
    )


# Export the prompt function
CreateMalloyQueryPrompt = create_malloy_query

__all__ = ["CreateMalloyQueryPrompt"]
