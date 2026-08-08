from middleware.base.tool_middleware import ToolMiddleware, NextHandler
from orchestrator.request_context import RequestContext

class AuthError(Exception):
    code = "auth_error"
    retryable = False

    def __init__(self, message: str):
        super().__init__(message)
        self.details = []

class AuthMiddleware(ToolMiddleware):
    async def process(
        self,
        context: RequestContext,
        next_handler: NextHandler,
    ):
        protected_tools = {
            "biosamples_submitsample",
        }

        if context.tool_name not in protected_tools:
            context.authenticated = True
            context.user_id = "anonymous-user"
            return await next_handler(context)

        webin_id = context.payload.get("webinId")

        if not webin_id:
            raise AuthError("Webin ID is required for this tool.")

        context.authenticated = True
        context.user_id = webin_id

        return await next_handler(context)