from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class RequestContext:
    request_id: str
    tool_name: str
    payload: dict[str, Any]
    authenticated: bool = False
    user_id: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))