import json
import pytest

from unittest.mock import AsyncMock
from middleware.cache_middleware import CacheMiddleware
from orchestrator.request_context import RequestContext

@pytest.mark.asyncio
async def test_cache_middleware_skips_non_cacheable_tool(async_next_handler):
    redis = AsyncMock()
    context = RequestContext("rid", "biosamples_submitsample", {"x": 1})
    middleware = CacheMiddleware(redis)

    result = await middleware.process(context, async_next_handler)

    assert result == {"ok": True}
    redis.get.assert_not_called()
    redis.set.assert_not_called()

@pytest.mark.asyncio
async def test_cache_middleware_skips_when_redis_is_none(async_next_handler):
    context = RequestContext("rid", "biosamples.search_samples", {"x": 1})
    middleware = CacheMiddleware(None)

    result = await middleware.process(context, async_next_handler)

    assert result == {"ok": True}
    async_next_handler.assert_awaited_once_with(context)

@pytest.mark.asyncio
async def test_cache_middleware_returns_cached_value(async_next_handler):
    redis = AsyncMock()
    redis.get.return_value = json.dumps({"cached": True})
    context = RequestContext("rid", "biosamples.search_samples", {"query": "blood"})
    middleware = CacheMiddleware(redis)

    result = await middleware.process(context, async_next_handler)

    assert result == {"cached": True}
    async_next_handler.assert_not_awaited()
    redis.set.assert_not_called()

@pytest.mark.asyncio
async def test_cache_middleware_writes_live_response_on_miss(async_next_handler):
    redis = AsyncMock()
    redis.get.return_value = None
    context = RequestContext("rid", "biosamples.search_samples", {"query": "blood"})
    middleware = CacheMiddleware(redis, ttl_seconds=123)

    result = await middleware.process(context, async_next_handler)

    assert result == {'ok': True}
    redis.set.assert_awaited_once()
    args = redis.set.await_args.args
    assert json.loads(args[1]) == {'ok': True}
    assert args[2] == 123

@pytest.mark.asyncio
async def test_cache_middleware_ignores_redis_read_error(async_next_handler):
    redis = AsyncMock()
    redis.get.side_effect = RuntimeError("redis down")
    context = RequestContext("rid", "biosamples.search_samples", {"query": "blood"})
    middleware = CacheMiddleware(redis)

    result = await middleware.process(context, async_next_handler)

    assert result == {"ok": True}
    async_next_handler.assert_awaited_once_with(context)

def test_cache_key_is_stable_for_same_payload_order():
    middleware = CacheMiddleware(None)
    first = RequestContext("rid", "tool", {"b": 2, "a": 1})
    second = RequestContext("rid", "tool", {"a": 1, "b": 2})

    assert middleware._cache_key(first) == middleware._cache_key(second)
    assert middleware._cache_key(first).startswith("tool-cache:tool:")