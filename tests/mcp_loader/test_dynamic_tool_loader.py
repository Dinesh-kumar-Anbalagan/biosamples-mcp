import inspect
import pytest

from unittest.mock import AsyncMock

from mcp_loader.dynamic_tool_loader import DynamicToolLoader

class Provider:
    def __init__(self, provides):
        self.provides = provides

class MCP:
    def __init__(self):
        self.tools = []

    def add_tool(self, **kwargs):
        self.tools.append(kwargs)

class Container:
    def __init__(self, providers):
        self.providers = providers

@pytest.mark.asyncio
async def test_create_tool_handler_passes_kwargs_to_orchestrator():
    orchestrator = AsyncMock()
    orchestrator.execute.return_value = {"ok": True}
    loader = DynamicToolLoader(MCP(), orchestrator, Container({}))

    handler = loader.create_tool_handler("tool")
    result = await handler(query="blood")

    assert result == {"ok": True}
    orchestrator.execute.assert_awaited_once_with(
        tool_name="tool",
        payload={"query": "blood"},
    )

@pytest.mark.asyncio
async def test_create_tool_handler_supports_nested_kwargs_payload():
    orchestrator = AsyncMock()
    orchestrator.execute.return_value = {"ok": True}
    loader = DynamicToolLoader(MCP(), orchestrator, Container({}))

    handler = loader.create_tool_handler("tool")
    await handler(kwargs={"query": "blood"})

    orchestrator.execute.assert_awaited_once_with(
        tool_name="tool",
        payload={"query": "blood"},
    )

def test_schema_to_signature_maps_json_schema_types():
    loader = DynamicToolLoader(MCP(), AsyncMock(), Container({}))
    schema = {
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "page": {"type": "integer", "default": 0},
            "filters": {"type": "array"},
        },
        "required": ["query"],
    }

    signature = loader.schema_to_signature(schema)

    assert signature.parameters["query"].default is inspect.Parameter.empty
    assert signature.parameters["query"].annotation is str
    assert signature.parameters["page"].default == 0
    assert signature.parameters["page"].annotation is int
    assert signature.parameters["filters"].default is None
    assert signature.parameters["filters"].annotation is list

def test_register_tools_adds_only_decorated_tools():
    class ToolClass:
        __is_tool__ = True
        __tool_name__ = "decorated_tool"
        __tool_description__ = "desc"
        __input_schema__ = {"type": "object", "properties": {}}

    class NotATool:
        pass

    mcp = MCP()
    container = Container(
        {
            "tool_provider": Provider(ToolClass),
            "other_provider": Provider(NotATool),
        }
    )
    loader = DynamicToolLoader(mcp, AsyncMock(), container)

    loader.register_tools()

    assert len(mcp.tools) == 1
    assert mcp.tools[0]["name"] == "decorated_tool"
    assert mcp.tools[0]["description"] == "desc"
    assert callable(mcp.tools[0]["fn"])