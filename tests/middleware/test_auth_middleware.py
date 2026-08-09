import pytest

from middleware.auth_middleware import AuthError, AuthMiddleware
from orchestrator.request_context import RequestContext

@pytest.mark.asyncio
async def test_auth_middleware_allows_unprotected_tool(async_next_handler):
    context = RequestContext("rid", "biosamples.search_samples", {})
    middleware = AuthMiddleware()

    result = await middleware.process(context, async_next_handler)

    assert result == {"ok": True}
    assert context.authenticated is True
    assert context.user_id == "anonymous-user"
    async_next_handler.assert_awaited_once_with(context)

@pytest.mark.asyncio
async def test_auth_middleware_rejects_submit_without_webin_id(async_next_handler):
    context = RequestContext("rid", "biosamples_submitsample", {})
    middleware = AuthMiddleware()

    with pytest.raises(AuthError) as exc:
        await middleware.process(context, async_next_handler)

    assert "Webin ID is required" in str(exc.value)
    assert exc.value.retryable is False
    async_next_handler.assert_not_awaited()

@pytest.mark.asyncio
async def test_auth_middleware_rejects_submit_with_webin_id(async_next_handler):
    context = RequestContext("rid", "biosamples_submitsample", {"webinId": "Webin-12345"})
    middleware = AuthMiddleware()

    result = await middleware.process(context, async_next_handler)

    assert result == {"ok": True}
    assert context.authenticated is True
    assert context.user_id == "Webin-12345"
    async_next_handler.assert_awaited_once_with(context)