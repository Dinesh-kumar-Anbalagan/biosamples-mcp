from typing import Any

from core.decorators import Tool
from orchestrator.request_context import RequestContext
from tools.base.tool_service import ToolService

@Tool(
    name="biosamples_serverinfo",
    description=(
            "Return basic information about the BioSamples MCP server. "
            "Use this tool when the user or MCP client wants to inspect the server name, "
            "server version, read-only/write mode status, supported BioSamples tools, "
            "and high-level server capabilities. "
            "Input: this tool does not require any input parameters. "
            "Example input payload: {}. "
            "This tool is read-only and does not call the BioSamples API, search samples, "
            "retrieve sample records, prepare submissions, validate drafts, or submit samples."
    ),
)
class ServerInfoToolService(ToolService):
    async def execute(
        self,
        context: RequestContext,
        payload: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "serverName": "BioSamples MCP Server",
            "version": "0.1.0",
            "supportedTools": [
                "biosamples.server_info",
                "biosamples.submit_sample",
                "biosamples.search_samples",
                "biosamples.get_sample",
            ],
        }