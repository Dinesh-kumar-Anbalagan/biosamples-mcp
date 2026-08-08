from unittest.mock import AsyncMock

import pytest

from middleware.logging_middleware import LoggingMiddleware
from orchestrator.request_context import RequestContext


@pytest.mark.asyncio
async def test_logging_middleware_returns_next_handler_result():
    context = RequestContext("rid", "tool", {"x": 1})
    next_handler = AsyncMock(return_value={"ok": True})

    result = await LoggingMiddleware().process(context, next_handler)

    assert result == {"ok": True}
    next_handler.assert_awaited_once_with(context)


@pytest.mark.asyncio
async def test_logging_middleware_re_raises_exception():
    context = RequestContext("rid", "tool", {"x": 1})
    next_handler = AsyncMock(side_effect=RuntimeError("boom"))

    with pytest.raises(RuntimeError, match="boom"):
        await LoggingMiddleware().process(context, next_handler)
