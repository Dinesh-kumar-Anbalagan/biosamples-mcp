from core.logger import get_logger

logger = get_logger(__name__)

class ToolExecutor:
    def __init__(self, container):
        self.container = container

    async def execute(self, context):
        logger.info(
            "Executing tool",
            extra={
                "extra_fields": {
                    "event": "tool_executor_started",
                    "tool": context.tool_name,
                    "requestId": context.request_id,
                }
            },
        )

        provider = self.container.providers.get(
            context.tool_name
        )

        if provider is None:
            raise ValueError(
                f"Tool '{context.tool_name}' not registered"
            )

        tool = provider()

        return await tool.execute(
            context,
            context.payload
        )