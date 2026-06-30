from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Any
from orchestrator.request_context import RequestContext

NextHandler = Callable[[RequestContext], Awaitable[dict[str, Any]]]

class ToolMiddleware(ABC):
    @abstractmethod
    async def process(
        self,
        context: RequestContext,
        next_handler: NextHandler,
    ) -> dict[str, Any]:
        pass