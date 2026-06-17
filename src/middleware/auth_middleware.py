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
            "biosamples.submit_sample",
        }

        if context.tool_name not in protected_tools:
            context.authenticated = True
            context.user_id = "anonymous-user"
            return await next_handler(context)

        auth_token = context.payload.get("authToken")

        if not auth_token:
            raise AuthError("Authentication token is required for this tool.")

        context.authenticated = True
        context.user_id = "authenticated-user"

        return await next_handler(context)