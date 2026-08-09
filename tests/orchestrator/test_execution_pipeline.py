import pytest

from orchestrator.execution_pipeline import ExecutionPipeline
from orchestrator.request_context import RequestContext

class RecordingMiddleware:
    def __init__(self, name, calls):
        self.name = name
        self.calls = calls

    async def process(self, context, next_handler):
        self.calls.append(f"before-{self.name}")
        result = await next_handler(context)
        self.calls.append(f"after-{self.name}")
        return result

class Executor:
    def __init__(self, calls):
        self.calls = calls

    async def execute(self, context):
        self.calls.append("executor")
        return {"done": context.tool_name}

@pytest.mark.asyncio
async def test_execution_pipeline_runs_middlewares_in_order():
    calls = []
    pipeline = ExecutionPipeline(
        middlewares=[RecordingMiddleware("one", calls), RecordingMiddleware("two", calls)],
        executor=Executor(calls),
    )
    context = RequestContext("rid", "tool", {})

    result = await pipeline.execute(context)

    assert result == {"done": "tool"}
    assert calls == ["before-one", "before-two", "executor", "after-two", "after-one"]

@pytest.mark.asyncio
async def test_execution_pipeline_without_middlewares_calls_executor():
    calls = []
    pipeline = ExecutionPipeline(middlewares=[], executor=Executor(calls))

    result = await pipeline.execute(RequestContext("rid", "tool", {}))

    assert result == {"done": "tool"}
    assert calls == ["executor"]