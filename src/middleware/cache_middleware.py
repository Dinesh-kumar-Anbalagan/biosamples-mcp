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
            "biosamples.submit_sample",
            "biosamples.prepare_submission",
        }

        if context.tool_name in non_cacheable:
            return await next_handler(context)

        if self.redis is None:
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
        except Exception:
            cached = None

        if cached and cached is not None:
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

        logger.info({
            "event": "cache_miss",
            "tool": context.tool_name,
            "cache": {
            "hit": False,
            "type": "redis",
            "ttlSeconds": self.ttl_seconds,
        },
        })
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