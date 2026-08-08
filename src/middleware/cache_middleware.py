import hashlib
import json

from core.logger import get_logger
from middleware.base.tool_middleware import ToolMiddleware, NextHandler
from orchestrator.request_context import RequestContext

logger = get_logger(__name__)

class CacheMiddleware(ToolMiddleware):
    def __init__(
        self,
        redis_client,
        ttl_seconds: int = 300,
    ):
        self.redis = redis_client
        self.ttl_seconds = ttl_seconds

    async def process(
        self,
        context: RequestContext,
        next_handler: NextHandler,
    ):
        logger.info("RedisCacheMiddleware")
        non_cacheable = {
            "biosamples_submitsample",
        }

        if context.tool_name in non_cacheable:
            logger.info(
                "Skipping cache for non-cacheable tool",
                extra={
                    "extra_fields": {
                        "event": "cache_skipped",
                        "tool": context.tool_name,
                        "requestId": context.request_id,
                    }
                },
            )
            return await next_handler(context)

        if self.redis is None:
            logger.info(
                "Skipping cache because Redis client is unavailable",
                extra={
                    "extra_fields": {
                        "event": "cache_unavailable",
                        "tool": context.tool_name,
                        "requestId": context.request_id,
                    }
                },
            )
            return await next_handler(context)

        cache_key = self._cache_key(context)

        logger.info(
            "Cache check started",
            extra={
                "extra_fields": {
                    "event": "cache_check_started",
                    "tool": context.tool_name,
                    "requestId": context.request_id,
                }
            },
        )

        try:
            cached = await self.redis.get(cache_key)
        except Exception as error:
            logger.warning(
                "Redis cache unavailable. Continuing without cache.",
                extra={
                    "extra_fields": {
                        "event": "cache_read_failed",
                        "tool": context.tool_name,
                        "requestId": context.request_id,
                        "error": str(error),
                    }
                },
            )

            return await next_handler(context)

        if cached is not None:
            logger.info(
                "Cache hit",
                extra={
                     "extra_fields": {
                        "event": "cache_hit",
                        "tool": context.tool_name,
                         "requestId": context.request_id,
                    }
                },
            )
            return json.loads(cached)

        response = await next_handler(context)

        try:
            await self.redis.setex(
                cache_key,
                self.ttl_seconds,
                json.dumps(response, default=str),
            )
        except Exception as error:
            logger.warning(
                "Redis cache write failed. Returning live response.",
                extra={
                    "extra_fields": {
                        "event": "cache_write_failed",
                        "tool": context.tool_name,
                        "requestId": context.request_id,
                        "error": str(error),
                    }
                },
            )
        return response

    def _cache_key(self, context: RequestContext) -> str:
        raw = json.dumps(
            {
                "tool": context.tool_name,
                "payload": context.payload,
            },
            sort_keys=True,
            default=str,
        )

        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()

        return f"tool-cache:{context.tool_name}:{digest}"