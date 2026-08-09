from datetime import timezone
from orchestrator.request_context import RequestContext

def test_request_context_defaults():
    context = RequestContext("rid", "tool", {"x": 1})

    assert context.request_id == "rid"
    assert context.tool_name == "tool"
    assert context.payload == {"x": 1}
    assert context.authenticated is False
    assert context.user_id is None
    assert context.timestamp.tzinfo == timezone.utc