import time
from typing import Any, Awaitable, Callable

from core.logger import get_logger
from orchestrator.request_context import RequestContext

logger = get_logger(__name__)


class LoggingMiddleware:
    async def process(
        self,
        context: RequestContext,
        next_handler: Callable[[RequestContext], Awaitable[dict[str, Any]]],
    ) -> dict[str, Any]:

        start = time.perf_counter()

        logger.info(
            "Tool execution started",
            extra={
                "extra_fields": {
                    "event": "tool_started",
                    "requestId": context.request_id,
                    "payloadKeys": list(context.payload.keys()),
                    "tool": context.tool_name,
                }
            },
        )

        try:
            result = await next_handler(context)

            duration_ms = int((time.perf_counter() - start) * 1000)

            logger.info(
                "Tool execution completed",
                extra={
                    "extra_fields": {
                        "event": "tool_completed",
                        "tool": context.tool_name,
                        "durationMs": duration_ms,
                    }
                },
            )

            return result

        except Exception:
            duration_ms = int((time.perf_counter() - start) * 1000)

            logger.exception(
                "Tool execution failed",
                extra={
                    "extra_fields": {
                        "event": "tool_failed",
                        "requestId": context.request_id,
                        "tool": context.tool_name,
                        "durationMs": duration_ms,
                    }
                },
            )

            raise