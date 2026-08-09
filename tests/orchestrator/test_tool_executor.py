import pytest

from unittest.mock import AsyncMock
from orchestrator.request_context import RequestContext
from orchestrator.tool_executor import ToolExecutor

class Provider:
    def __init__(self, tool):
        self.tool = tool

    def __call__(self):
        return self.tool

class Container:
    def __init__(self, providers):
        self.providers = providers

@pytest.mark.asyncio
async def test_tool_executor_executes_registered_tool():
    tool = AsyncMock()
    tool.execute.return_value = {"ok": True}
    container = Container({"tool": Provider(tool)})
    context = RequestContext("rid", "tool", {"x": 1})

    result = await ToolExecutor(container).execute(context)

    assert result == {"ok": True}
    tool.execute.assert_awaited_once_with(context, {"x": 1})

@pytest.mark.asyncio
async def test_tool_executor_raises_for_missing_tool():
    container = Container({})
    context = RequestContext("rid", "missing", {})

    with pytest.raises(ValueError, match="Tool 'missing' not registered"):
        await ToolExecutor(container).execute(context)