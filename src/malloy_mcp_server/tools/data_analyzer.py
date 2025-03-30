"""Tool for analyzing data returned from Malloy queries using Polars and Plotly."""

from typing import Any, Dict, List, Optional

import plotly.express as px
import polars as pl
from mcp.server.context import Context
from mcp.server.errors import ToolError
from mcp.server.fastmcp import FastMCP

# Initialize MCP
mcp = FastMCP("Data Analyzer")

# Supported visualization types
SUPPORTED_VIZ_TYPES = ["line", "bar", "scatter", "box"]


@mcp.tool()
async def analyze_data(
    df: pl.DataFrame,
    analysis_type: str,
    columns: List[str],
    ctx: Context,
    viz_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze data based on specified parameters.

    Args:
        df: The DataFrame to analyze
        analysis_type: Type of analysis to perform
        columns: Columns to analyze
        ctx: The MCP context for logging and progress tracking
        viz_type: Type of visualization to generate

    Returns:
        Analysis results

    Raises:
        ToolError: If analysis fails
    """
    try:
        await ctx.info(
            f"Starting {analysis_type} analysis on columns: {', '.join(columns)}"
        )

        result: Dict[str, Any] = {}

        if analysis_type == "summary":
            result["summary"] = _generate_summary(df, columns)
        elif analysis_type == "correlation":
            result["correlation"] = _analyze_correlation(df, columns)
        elif analysis_type == "trend":
            result["trend"] = _analyze_trends(df, columns)
        else:
            raise ValueError(f"Unsupported analysis type: {analysis_type}")

        if viz_type and viz_type in SUPPORTED_VIZ_TYPES:
            result["visualization"] = _create_visualization(df, columns, viz_type)

        await ctx.info("Analysis completed successfully")
        return result

    except Exception as e:
        error_msg = f"Failed to analyze data: {e!s}"
        await ctx.error(error_msg)
        raise ToolError(
            message=error_msg,
            context={
                "analysis_type": analysis_type,
                "columns": columns,
                "visualization_type": viz_type,
            },
        ) from e


def _generate_summary(df: pl.DataFrame, columns: List[str]) -> Dict[str, float]:
    """Generate summary statistics."""
    result: Dict[str, float] = {}
    for col in columns:
        stats = df.select(pl.col(col)).describe()
        result[f"{col}_mean"] = float(
            stats.filter(pl.col("statistic") == "mean")["value"][0]
        )
        result[f"{col}_std"] = float(
            stats.filter(pl.col("statistic") == "std")["value"][0]
        )
        result[f"{col}_min"] = float(
            stats.filter(pl.col("statistic") == "min")["value"][0]
        )
        result[f"{col}_max"] = float(
            stats.filter(pl.col("statistic") == "max")["value"][0]
        )
        # Calculate quartiles
        series = df.select(pl.col(col)).to_series()
        q1 = series.quantile(0.25)
        q3 = series.quantile(0.75)
        result[f"{col}_q1"] = float(q1) if q1 is not None else 0.0
        result[f"{col}_q3"] = float(q3) if q3 is not None else 0.0
    return result


def _analyze_correlation(df: pl.DataFrame, columns: List[str]) -> Dict[str, float]:
    """Calculate correlations between columns."""
    result: Dict[str, float] = {}
    for i, col1 in enumerate(columns):
        for col2 in columns[i + 1 :]:
            corr = df.select([pl.col(col1), pl.col(col2)]).corr()
            if corr is not None and len(corr) > 0:
                result[f"{col1}_{col2}"] = float(corr[0, 1])
            else:
                result[f"{col1}_{col2}"] = 0.0
    return result


def _analyze_trends(df: pl.DataFrame, columns: List[str]) -> Dict[str, List[float]]:
    """Analyze trends in numeric columns."""
    metric_cols = columns[1:]  # First column assumed to be time/sequence
    result: Dict[str, List[float]] = {}
    for col in metric_cols:
        series = df.select(pl.col(col)).to_series()
        values = series.to_list()
        result[f"{col}_values"] = [float(x) if x is not None else 0.0 for x in values]
    return result


def _create_visualization(
    df: pl.DataFrame, columns: List[str], viz_type: str
) -> Dict[str, Any]:
    """Create a visualization of the data."""
    # Convert to pandas for Plotly compatibility
    pdf = df.select(columns).to_pandas()

    if viz_type == "line":
        fig = px.line(pdf, x=columns[0], y=columns[1:])
    elif viz_type == "bar":
        fig = px.bar(pdf, x=columns[0], y=columns[1:])
    elif viz_type == "scatter":
        fig = px.scatter(pdf, x=columns[0], y=columns[1])
    elif viz_type == "box":
        fig = px.box(pdf, y=columns[0])

    return {
        "plot": fig.to_json(),
        "type": viz_type,
    }
