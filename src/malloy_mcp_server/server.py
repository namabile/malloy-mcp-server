"""
Malloy MCP Server implementation using the official MCP Python SDK.
Provides tools and prompts for interacting with Malloy data models.
"""

from typing import Any, Dict, List, Optional, TypeVar, Generic, Protocol

from malloy_publisher_client import MalloyPublisherClient
from mcp.server.fastmcp import FastMCP
from mcp.server.context import Context
from pydantic import BaseModel

from .models.resources import (
    MalloyModelMetadata,
    MalloyPackageMetadata,
    MalloyProjectMetadata,
)

T = TypeVar("T")

class TypedContext(Protocol, Generic[T]):
    async def error(self, message: str) -> None: ...
    async def info(self, message: str) -> None: ...

# Initialize MCP server with proper capabilities
mcp = FastMCP(
    name="malloy-mcp-server",
    description="MCP server for Malloy data analysis and query execution",
    capabilities={
        "prompts": {"listChanged": True},
        "resources": {"subscribelistChanged": True},
        "tools": {"listChanged": True},
        "logging": True,
        "completion": True,
    },
)

# Initialize Malloy publisher client
client = MalloyPublisherClient("http://localhost:4000")
PROJECT_NAME = "home"


# Input/Output models for tools
class MalloyQueryInput(BaseModel):
    """Input parameters for Malloy query execution."""

    query: str
    model_path: str


class MalloyQueryOutput(BaseModel):
    """Output from Malloy query execution."""

    results: list[dict[str, Any]]


class DataAnalysisInput(BaseModel):
    """Input parameters for data analysis."""

    data: list[dict[str, Any]]
    analysis_type: str
    columns: list[str]
    visualization_type: str | None = None


class DataAnalysisOutput(BaseModel):
    """Output from data analysis."""

    summary: dict[str, Any] | None = None
    correlation: dict[str, float] | None = None
    distribution: dict[str, Any] | None = None
    trend: dict[str, Any] | None = None
    visualization: dict[str, Any] | None = None


@mcp.tool()
async def execute_malloy_query(
    params: MalloyQueryInput, ctx: Context
) -> MalloyQueryOutput:
    """Execute a Malloy query against available data models.

    Args:
        params: The query parameters including the query string and model path
        ctx: The MCP context for progress reporting and error handling

    Returns:
        The query results wrapped in a MalloyQueryOutput model

    Raises:
        ValueError: If the query execution fails with a user-friendly error message
    """
    try:
        ctx.info(f"Executing Malloy query against model {params.model_path}")

        # Report start of query execution
        await ctx.report_progress(0, 2)

        result = await client.run_query(
            project=PROJECT_NAME, model_path=params.model_path, query=params.query
        )

        # Report query completion
        await ctx.report_progress(1, 2)

        ctx.info(f"Query executed successfully, processing {len(result)} rows")

        # Report final completion
        await ctx.report_progress(2, 2)

        return MalloyQueryOutput(results=result)

    except Exception as e:
        error_context = {
            "query": params.query,
            "model_path": params.model_path,
            "project": PROJECT_NAME,
        }
        error_msg = (
            f"Failed to execute Malloy query: {e!s}\nContext: {error_context}"
        )
        await ctx.error(error_msg)
        raise ValueError(error_msg) from None


@mcp.tool()
async def analyze_data(params: DataAnalysisInput, ctx: TypedContext[DataAnalysisOutput]) -> DataAnalysisOutput:
    """Analyze and visualize data from Malloy query results."""
    import plotly.express as px
    import polars as pl

    try:
        # Convert data to Polars DataFrame
        df = pl.DataFrame(params.data)
        result = DataAnalysisOutput()

        # Perform requested analysis
        if params.analysis_type == "summary":
            summary_result: Dict[str, float] = {}
            summary_data = df.describe()
            for col in params.columns:
                col_stats = summary_data[col]
                summary_result[f"{col}_mean"] = float(col_stats.loc["mean"])
                summary_result[f"{col}_std"] = float(col_stats.loc["std"])
                summary_result[f"{col}_min"] = float(col_stats.loc["min"])
                summary_result[f"{col}_max"] = float(col_stats.loc["max"])
                summary_result[f"{col}_q1"] = float(col_stats.quantile(0.25))
                summary_result[f"{col}_q3"] = float(col_stats.quantile(0.75))
            return DataAnalysisOutput(summary=summary_result)

        elif params.analysis_type == "correlation":
            numeric_cols = [
                col
                for col in params.columns
                if df[col].dtype in [pl.Float32, pl.Float64, pl.Int32, pl.Int64]
            ]
            result.correlation = df.select(numeric_cols).corr().to_dict(as_series=False)

        elif params.analysis_type == "distribution":
            dist_data = {}
            for col in params.columns:
                dist_data[col] = {
                    "unique_count": df[col].n_unique(),
                    "null_count": df[col].null_count(),
                    "quantiles": df[col].quantile([0.25, 0.5, 0.75]).to_list(),
                }
            result.distribution = dist_data

        elif params.analysis_type == "trend":
            trend_data = {}
            sequence_col = params.columns[0]
            metric_cols = params.columns[1:]

            for col in metric_cols:
                trend_data[col] = {
                    "first_value": df[col].first(),
                    "last_value": df[col].last(),
                    "change": float(df[col].last() - df[col].first()),
                    "pct_change": float(
                        (df[col].last() - df[col].first()) / df[col].first() * 100
                    ),
                }
            result.trend = trend_data

        # Generate visualization if requested
        if params.visualization_type:
            pdf = df.select(params.columns).to_pandas()

            if params.visualization_type == "line":
                fig = px.line(pdf, x=params.columns[0], y=params.columns[1:])
            elif params.visualization_type == "bar":
                fig = px.bar(pdf, x=params.columns[0], y=params.columns[1:])
            elif params.visualization_type == "scatter":
                fig = px.scatter(pdf, x=params.columns[0], y=params.columns[1])
            elif params.visualization_type == "histogram":
                fig = px.histogram(pdf, x=params.columns[0])
            elif params.visualization_type == "box":
                fig = px.box(pdf, y=params.columns[0])

            result.visualization = {
                "plot": fig.to_json(),
                "type": params.visualization_type,
            }

        return result

    except Exception as e:
        error_msg = f"Failed to analyze data: {e!s}"
        await ctx.error(error_msg)
        raise ValueError(error_msg) from e


@mcp.prompt()
async def create_malloy_query(
    model_path: str, requirements: str, available_sources: list[str]
) -> dict[str, str]:
    """Create a Malloy query based on the available models and requirements."""
    try:
        # Build context for query generation
        context = {
            "model_path": model_path,
            "requirements": requirements,
            "sources": available_sources,
            "best_practices": [
                "Use clear and descriptive names for dimensions and measures",
                "Leverage Malloy's nested queries for complex analysis",
                "Use appropriate aggregations based on data types",
                "Include relevant filters to focus the analysis",
                "Consider performance implications of joins and aggregations",
            ],
        }

        # Generate query (placeholder implementation)
        query = f"""
        query: {context['sources'][0]} ->
        {{
            group_by: dimension1
            aggregate:
                measure1
        }}
        """

        return {
            "query": query,
            "explanation": (
                "This query groups the data by dimension1 and calculates "
                "measure1 for each group."
            ),
        }

    except Exception as e:
        error_msg = f"Failed to generate Malloy query: {e!s}"
        await ctx.error(error_msg)
        raise ValueError(error_msg) from e


# Register resources
@mcp.on_startup
async def register_resources() -> None:
    """Register available Malloy resources with the MCP server."""
    try:
        # Get project metadata
        project = await client.get_project(PROJECT_NAME)

        # Get packages in the project
        packages = await client.list_packages(PROJECT_NAME)
        package_metadata = []

        for pkg in packages:
            # Get models in the package
            models = await client.list_models(PROJECT_NAME, pkg.name)
            pkg_meta = MalloyPackageMetadata(
                name=pkg.name,
                description=pkg.description,
                version=pkg.version,
                models=[model.path for model in models],
            )
            package_metadata.append(pkg_meta)

        # Get all models and their metadata
        model_metadata = []
        for pkg in packages:
            models = await client.list_models(PROJECT_NAME, pkg.name)
            for model in models:
                # Get model details including sources and schema
                model_details = await client.get_model(
                    PROJECT_NAME, pkg.name, model.path
                )
                model_meta = MalloyModelMetadata(
                    path=model.path,
                    description=model.description,
                    sources=model_details.sources,
                    queries=model_details.queries,
                    schema=model_details.schema,
                )
                model_metadata.append(model_meta)

        # Create project metadata resource
        project_meta = MalloyProjectMetadata(
            name=PROJECT_NAME,
            description=project.description,
            packages=package_metadata,
            models=model_metadata,
        )

        # Register resources with proper URIs
        mcp.add_resource(
            name="malloy://project/home/metadata",
            description="Metadata about the Malloy project and its contents",
            data=project_meta.model_dump(),
            version="1.0",
        )

        # Register each package as a resource
        for pkg in package_metadata:
            mcp.add_resource(
                name=f"malloy://project/home/package/{pkg.name}",
                description=f"Metadata for the {pkg.name} package",
                data=pkg.model_dump(),
                version=pkg.version or "1.0",
            )

        # Register each model as a resource
        for model in model_metadata:
            mcp.add_resource(
                name=f"malloy://project/home/model/{model.path}",
                description=f"Metadata for the model at {model.path}",
                data=model.model_dump(),
                version="1.0",
            )

    except Exception as e:
        error_msg = f"Failed to register Malloy resources: {e!s}"
        mcp.logger.error(error_msg)
        raise RuntimeError(error_msg) from e


# Export the FastMCP instance
__all__ = ["mcp"]
