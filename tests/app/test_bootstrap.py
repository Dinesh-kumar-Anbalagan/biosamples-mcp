import pytest

from app import bootstrap
from core.config import Settings
from unittest.mock import Mock, patch
from app.bootstrap import build_application
from orchestrator.mcp_tool_orchestrator import MCPToolOrchestrator

pytest.importorskip("redis")

def test_build_application_returns_orchestrator(monkeypatch):
    container = Mock()
    mocked_settings = Settings(
        cache_enabled=False,
    )

    monkeypatch.setattr(
        bootstrap,
        "settings",
        mocked_settings,
    )

    with patch("app.bootstrap.create_redis_client", return_value=None):
        app = build_application(container)

    assert isinstance(app, MCPToolOrchestrator)
    assert len(app.pipeline.middlewares) == 2
    assert app.pipeline.executor.container is container
