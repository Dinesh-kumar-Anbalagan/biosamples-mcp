from mcp.server.fastmcp import FastMCP
from app.bootstrap import build_application
from core.logger import get_logger, configure_logging
from mcp_loader.dynamic_tool_loader import DynamicToolLoader
from mcp_loader.container_builder import ContainerBuilder

configure_logging("INFO")

logger = get_logger(__name__)
logger.info("Starting BioSamples MCP server...")

mcp = FastMCP(name="BioSamples MCP Server")

container = ContainerBuilder(packages=[
        "adapter",
        "tools"
    ]).build_container()

orchestrator = build_application(container)

DynamicToolLoader(
    mcp=mcp,
    orchestrator=orchestrator,
    container = container,
).register_tools()

if __name__ == "__main__":
    mcp.run()