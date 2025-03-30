"""Prompt for assisting in creating Malloy queries."""

from typing import Any

from mcp import Prompt, PromptCall, PromptError, PromptResult


class CreateMalloyQueryPrompt(Prompt):
    """Prompt for creating Malloy queries based on user requirements."""

    def __init__(self) -> None:
        """Initialize the query creation prompt."""
        super().__init__(
            name="create_malloy_query",
            description=(
                "Create a Malloy query based on the available models and requirements"
            ),
            parameters={
                "type": "object",
                "properties": {
                    "model_path": {
                        "type": "string",
                        "description": "Path to the Malloy model to query against",
                    },
                    "requirements": {
                        "type": "string",
                        "description": "Description of what data needs to be queried",
                    },
                    "available_sources": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of available sources in the model",
                    },
                },
                "required": ["model_path", "requirements", "available_sources"],
            },
        )

    async def execute(self, call: PromptCall) -> PromptResult:
        """Generate a Malloy query based on requirements.

        Args:
            call: The prompt call containing query requirements.

        Returns:
            Generated query as a PromptResult.

        Raises:
            PromptError: If query generation fails.
        """
        try:
            model_path = call.parameters["model_path"]
            requirements = call.parameters["requirements"]
            sources = call.parameters["available_sources"]

            # Build context for query generation
            context = self._build_context(model_path, requirements, sources)

            # Generate the query
            query = self._generate_query(context)

            return PromptResult(
                result={
                    "query": query,
                    "explanation": self._explain_query(query),
                }
            )

        except Exception as e:
            raise PromptError(
                message=f"Failed to generate Malloy query: {e!s}",
                context={
                    "model_path": model_path,
                    "requirements": requirements,
                    "available_sources": sources,
                },
            ) from e

    def _build_context(
        self, model_path: str, requirements: str, sources: list[str]
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

    def _generate_query(self, context: dict[str, Any]) -> str:
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

    def _explain_query(self, query: str) -> str:
        """Generate an explanation of the query."""
        # This is a placeholder - in a real implementation, this would
        # provide a clear explanation of what the query does and why
        # certain choices were made
        return (
            "This query groups the data by dimension1 and calculates "
            "measure1 for each group."
        )
