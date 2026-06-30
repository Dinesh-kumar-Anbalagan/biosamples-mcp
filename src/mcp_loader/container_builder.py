import importlib
import inspect
import pkgutil
import re

from dependency_injector import containers, providers
from core.decorators import component_registry, tool_registry

def import_all_modules(package_name: str) -> None:
    package = importlib.import_module(package_name)
    if not hasattr(package, "__path__"):
        raise ValueError(f"{package_name} is not a package")

    for module_info in pkgutil.walk_packages(
        package.__path__,
        prefix=package.__name__ + ".",
    ):
        if not module_info.ispkg:
            importlib.import_module(module_info.name)

def to_snake_case(name: str) -> str:
    name = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return name.lower()

class ContainerBuilder:
    def __init__(self, packages: str | list[str]):
        self.packages = [packages] if isinstance(packages, str) else packages

    def build_container(self):
        for package in self.packages:
            import_all_modules(package)

        container = containers.DynamicContainer()

        for cls in component_registry:
            provider = providers.Singleton(cls)
            setattr(container, cls.__component_name__, provider)

        for cls in tool_registry:
            name = getattr(cls, "__tool_name__", to_snake_case(cls.__name__))
            signature = inspect.signature(cls.__init__)
            dependencies = {}

            for param in signature.parameters.values():
                if param.name == "self":
                    continue

                if param.kind in (
                        inspect.Parameter.VAR_POSITIONAL,
                        inspect.Parameter.VAR_KEYWORD,
                ):
                    continue

                if param.default is not inspect.Parameter.empty:
                    continue

                if param.annotation is inspect.Parameter.empty:
                    raise TypeError(
                        f"Missing type annotation for '{param.name}' "
                        f"in {cls.__name__}.__init__"
                    )

                dependency_name = to_snake_case(param.annotation.__name__)

                if not hasattr(container, dependency_name):
                    raise ValueError(
                        f"Dependency '{dependency_name}' for {cls.__name__} "
                        f"is not registered yet"
                    )

                dependencies[param.name] = getattr(container, dependency_name)

            provider = providers.Singleton(cls, **dependencies)
            setattr(container, name, provider)

        return container