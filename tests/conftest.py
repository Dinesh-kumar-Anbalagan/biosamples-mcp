import sys
import types
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

class _FakeRedis:
    calls = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.storage = {}

    @classmethod
    def from_url(cls, *args, **kwargs):
        cls.calls.append((args, kwargs))
        return cls(*args, **kwargs)

    async def get(self, key):
        return self.storage.get(key)

    async def setex(self, key, ttl, value):
        self.storage[key] = value
        return True


class _SingletonProvider:
    def __init__(self, cls, **dependencies):
        self.cls = cls
        self.dependencies = dependencies
        self._instance = None

    def __call__(self):
        if self._instance is None:
            resolved = {
                name: provider() if callable(provider) else provider
                for name, provider in self.dependencies.items()
            }
            self._instance = self.cls(**resolved)
        return self._instance


class _DynamicContainer:
    pass


def _install_redis_shim():
    redis_module = sys.modules.get("redis") or types.ModuleType("redis")
    redis_asyncio_module = sys.modules.get("redis.asyncio") or types.ModuleType("redis.asyncio")
    redis_asyncio_module.Redis = _FakeRedis
    redis_module.asyncio = redis_asyncio_module
    sys.modules.setdefault("redis", redis_module)
    sys.modules.setdefault("redis.asyncio", redis_asyncio_module)


def _install_dependency_injector_shim():
    dependency_injector_module = sys.modules.get("dependency_injector") or types.ModuleType("dependency_injector")
    containers_module = types.ModuleType("dependency_injector.containers")
    providers_module = types.ModuleType("dependency_injector.providers")
    containers_module.DynamicContainer = _DynamicContainer
    providers_module.Singleton = _SingletonProvider
    dependency_injector_module.containers = containers_module
    dependency_injector_module.providers = providers_module
    sys.modules.setdefault("dependency_injector", dependency_injector_module)
    sys.modules.setdefault("dependency_injector.containers", containers_module)
    sys.modules.setdefault("dependency_injector.providers", providers_module)


_install_redis_shim()
_install_dependency_injector_shim()


@pytest.fixture
def request_context():
    from orchestrator.request_context import RequestContext

    return RequestContext(
        request_id="test-request-id",
        tool_name="test_tool",
        payload={"hello": "world"},
    )


@pytest.fixture
def async_next_handler():
    return AsyncMock(return_value={"ok": True})
