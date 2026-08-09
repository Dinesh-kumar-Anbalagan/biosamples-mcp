import pytest

from unittest.mock import AsyncMock, patch
from orchestrator.mcp_tool_orchestrator import MCPToolOrchestrator

@pytest.mark.asyncio
async def test_mcp_tool_orchestrator_creates_context_and_calls_pipeline():
    pipeline = AsyncMock()
    pipeline.execute.return_value = {"ok": True}
    orchestrator = MCPToolOrchestrator(pipeline)

    with patch("orchestrator.mcp_tool_orchestrator.uuid.uuid4", return_value="uuid-1"):
        result = await orchestrator.execute("tool_name", {"x": 1})

    assert result == {"ok": True}
    context = pipeline.execute.await_args.args[0]
    assert context.request_id == "uuid-1"
    assert context.tool_name == "tool_name"
    assert context.payload == {"x": 1}