from core.config import settings
from core.redis_client import create_redis_client
from orchestrator.execution_pipeline import ExecutionPipeline
from orchestrator.mcp_tool_orchestrator import MCPToolOrchestrator
from orchestrator.tool_executor import ToolExecutor
from middleware.auth_middleware import AuthMiddleware
from middleware.logging_middleware import LoggingMiddleware
from middleware.cache_middleware import CacheMiddleware

def build_application(container) -> MCPToolOrchestrator:
    tool_executor = ToolExecutor(container)

    redis_client = create_redis_client()
    middlewares = [
        LoggingMiddleware(),
        AuthMiddleware(),
        CacheMiddleware(
            redis_client=redis_client,
            ttl_seconds=settings.cache_ttl_seconds,),
    ]

    pipeline = ExecutionPipeline(
        middlewares=middlewares,
        executor=tool_executor,
    )

    return MCPToolOrchestrator(
        pipeline=pipeline,
    )