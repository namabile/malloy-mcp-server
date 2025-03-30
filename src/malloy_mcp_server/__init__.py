"""Malloy MCP server package."""

from .prompts.query_creator import CreateMalloyQueryPrompt
from .server import MalloyMCPServer, create_server
from .tools.data_analyzer import AnalyzeDataTool
from .tools.query_executor import ExecuteMalloyQueryTool

__version__ = "0.1.0"
__all__ = [
    "AnalyzeDataTool",
    "CreateMalloyQueryPrompt",
    "ExecuteMalloyQueryTool",
    "MalloyMCPServer",
    "create_server",
]
