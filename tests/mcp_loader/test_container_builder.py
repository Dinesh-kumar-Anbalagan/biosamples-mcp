import sys
import types

import pytest

pytest.importorskip("dependency_injector")

from core.decorators import component_registry, tool_registry
from mcp_loader.container_builder import ContainerBuilder, import_all_modules, to_snake_case


def test_to_snake_case():
    assert to_snake_case("BioSamplesAdapter") == "bio_samples_adapter"
    assert to_snake_case("MCPTool") == "mcp_tool"


def test_import_all_modules_rejects_non_package(monkeypatch):
    module = types.ModuleType("not_a_package")
    monkeypatch.setitem(sys.modules, "not_a_package", module)

    with pytest.raises(ValueError, match="not_a_package is not a package"):
        import_all_modules("not_a_package")


def test_container_builder_registers_component_and_tool(monkeypatch):
    component_registry.clear()
    tool_registry.clear()

    class ExampleComponent:
        __component_name__ = "example_component"

    class ExampleTool:
        __is_tool__ = True
        __tool_name__ = "example_tool"

        def __init__(self, example_component: ExampleComponent):
            self.example_component = example_component

    component_registry.append(ExampleComponent)
    tool_registry.append(ExampleTool)
    monkeypatch.setattr("mcp_loader.container_builder.import_all_modules", lambda package: None)

    container = ContainerBuilder("fake_package").build_container()

    assert hasattr(container, "example_component")
    assert hasattr(container, "example_tool")
    tool = container.example_tool()
    assert isinstance(tool.example_component, ExampleComponent)


def test_container_builder_raises_for_missing_annotation(monkeypatch):
    component_registry.clear()
    tool_registry.clear()

    class BadTool:
        __is_tool__ = True
        __tool_name__ = "bad_tool"

        def __init__(self, dependency):
            self.dependency = dependency

    tool_registry.append(BadTool)
    monkeypatch.setattr("mcp_loader.container_builder.import_all_modules", lambda package: None)

    with pytest.raises(TypeError, match="Missing type annotation"):
        ContainerBuilder("fake_package").build_container()


def test_container_builder_raises_for_missing_registered_dependency(monkeypatch):
    component_registry.clear()
    tool_registry.clear()

    class MissingDependency:
        pass

    class ToolWithMissingDependency:
        __is_tool__ = True
        __tool_name__ = "missing_dep_tool"

        def __init__(self, missing_dependency: MissingDependency):
            self.missing_dependency = missing_dependency

    tool_registry.append(ToolWithMissingDependency)
    monkeypatch.setattr("mcp_loader.container_builder.import_all_modules", lambda package: None)

    with pytest.raises(ValueError, match="Dependency 'missing_dependency'"):
        ContainerBuilder("fake_package").build_container()
