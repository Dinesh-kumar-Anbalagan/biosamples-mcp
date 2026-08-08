import json
import logging

from core.decorators import Component, Tool, component_registry, tool_registry
from core.logger import JsonFormatter, configure_logging, get_logger


def test_tool_decorator_adds_metadata_and_registers_class():
    start_len = len(tool_registry)

    @Tool(name="tool_name", description="desc", input_schema={"type": "object"})
    class ExampleTool:
        pass

    assert ExampleTool.__is_tool__ is True
    assert ExampleTool.__tool_name__ == "tool_name"
    assert ExampleTool.__tool_description__ == "desc"
    assert ExampleTool.__input_schema__ == {"type": "object"}
    assert tool_registry[-1] is ExampleTool
    assert len(tool_registry) == start_len + 1


def test_component_decorator_adds_metadata_and_registers_class():
    start_len = len(component_registry)

    @Component("example_component")
    class ExampleComponent:
        pass

    assert ExampleComponent.__component_name__ == "example_component"
    assert component_registry[-1] is ExampleComponent
    assert len(component_registry) == start_len + 1


def test_json_formatter_outputs_json_with_extra_fields():
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="file.py",
        lineno=10,
        msg="hello",
        args=(),
        exc_info=None,
    )
    record.extra_fields = {"requestId": "rid"}

    data = json.loads(JsonFormatter().format(record))

    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"
    assert data["message"] == "hello"
    assert data["requestId"] == "rid"


def test_configure_logging_sets_root_handler():
    configure_logging("DEBUG")

    root = logging.getLogger()
    assert root.level == logging.DEBUG
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)


def test_get_logger_returns_named_logger():
    assert get_logger("abc").name == "abc"
