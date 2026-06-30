from typing import Optional

tool_registry = []
component_registry = []

class Tool:
    def __init__(self, name: Optional[str] = None, description: str = "", input_schema: Optional[dict] = None):
        self.name = name
        self.description = description
        self.input_schema = input_schema

    def __call__(self, cls):
        cls.__is_tool__ = True
        cls.__tool_name__ = self.name
        cls.__tool_description__ = self.description
        cls.__input_schema__ = self.input_schema

        tool_registry.append(cls)

        return cls

class Component:
    def __init__(
        self,
        name: Optional[str] = None
    ):
        self.name = name

    def __call__(self, cls):
        cls.__component_name__ = self.name

        component_registry.append(cls)

        return cls