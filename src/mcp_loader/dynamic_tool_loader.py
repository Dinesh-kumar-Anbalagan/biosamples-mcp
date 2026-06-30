import inspect
from typing import Any, Awaitable, Callable

JSON_SCHEMA_TYPE_MAP = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "object": dict,
    "array": list,
}


class DynamicToolLoader:
    def __init__(
        self,
        mcp,
        orchestrator,
        container,
    ):
        self.mcp = mcp
        self.orchestrator = orchestrator
        self.container = container

    def schema_to_signature(
        self,
        input_schema: dict[str, Any],
    ) -> inspect.Signature:
        properties = input_schema.get("properties", {})
        required = set(input_schema.get("required", []))

        parameters = []

        for field_name, field_schema in properties.items():
            json_type = field_schema.get("type")
            annotation = JSON_SCHEMA_TYPE_MAP.get(json_type, Any)

            if field_name in required:
                default = inspect.Parameter.empty
            else:
                default = field_schema.get("default", None)

            parameters.append(
                inspect.Parameter(
                    name=field_name,
                    kind=inspect.Parameter.KEYWORD_ONLY,
                    annotation=annotation,
                    default=default,
                )
            )

        return inspect.Signature(
            parameters=parameters,
            return_annotation=dict[str, Any],
        )

    def create_tool_handler(
        self,
        tool_name: str,
        input_schema: dict[str, Any] | None = None,
    ) -> Callable[..., Awaitable[dict[str, Any]]]:

        async def handler(**kwargs: Any) -> dict[str, Any]:
            nested_kwargs = kwargs.get("kwargs")

            if isinstance(nested_kwargs, dict):
                payload = nested_kwargs
            else:
                payload = kwargs

            return await self.orchestrator.execute(
                tool_name=tool_name,
                payload=payload,
            )

        handler.__name__ = tool_name

        if input_schema is not None:
            handler.__signature__ = self.schema_to_signature(input_schema)

        return handler

    def register_tools(self) -> None:
        for name, provider in self.container.providers.items():
            cls = provider.provides

            is_tool = getattr(cls, "__is_tool__", False)
            if not is_tool:
                continue

            tool_name = getattr(cls, "__tool_name__", name)
            tool_description = getattr(cls, "__tool_description__", "")
            tool_input_schema = getattr(cls, "__input_schema__", None)

            handler = self.create_tool_handler(
                tool_name=tool_name,
                input_schema=tool_input_schema,
            )

            self.mcp.add_tool(
                fn=handler,
                name=tool_name,
                description=tool_description,
            )