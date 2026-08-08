import pytest

pytest.importorskip("redis")

from unittest.mock import Mock, patch

from app.bootstrap import build_application
from orchestrator.mcp_tool_orchestrator import MCPToolOrchestrator


def test_build_application_returns_orchestrator():
    container = Mock()

    with patch("app.bootstrap.create_redis_client", return_value=None):
        app = build_application(container)

    assert isinstance(app, MCPToolOrchestrator)
    assert len(app.pipeline.middlewares) == 2
    assert app.pipeline.executor.container is container
