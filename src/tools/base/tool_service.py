from abc import ABC, abstractmethod
from typing import Any

from orchestrator.request_context import RequestContext


class ToolService(ABC):
    @abstractmethod
    async def execute(
        self,
        context: RequestContext,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        pass