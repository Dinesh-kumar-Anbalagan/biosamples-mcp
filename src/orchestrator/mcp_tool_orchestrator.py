import uuid

from orchestrator.request_context import RequestContext

class MCPToolOrchestrator:
    def __init__(
        self,
        pipeline
    ):
        self.pipeline = pipeline

    async def execute(
        self,
        tool_name,
        payload
    ):
        context = RequestContext(
            request_id=str(uuid.uuid4()),
            tool_name=tool_name,
            payload=payload
        )

        return await self.pipeline.execute(
            context
        )