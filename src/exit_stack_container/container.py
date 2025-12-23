"""DI container with async lifecycle management."""

from __future__ import annotations

import inspect
from collections.abc import Awaitable
from contextlib import AsyncExitStack
from typing import Any, Callable

from msgspec_settings import BaseSettings

from .defaults import CLEANUP_ATTR_NAME
from .dependency import Dependency
from .exceptions import (
    CircularDependencyError,
    ContainerReuseError,
    InvalidContainerInheritance,
)
from .models import BaseResources
from .types import CleanupFn, DependencyGraph, ResolvedDeps


class AsyncExitStackContainer[T = BaseSettings, V = BaseResources]:
    """DI container with async lifecycle management."""

    _settings: T
    _stack: AsyncExitStack | None = None

    def __init__(self) -> None:
        """Initialize and scan dependencies."""
        self._resources_class: type[V] | None = None
        self._dependencies: dict[str, Dependency] = {}
        self._resolution_order: list[str] = []

    @property
    def resources_class(self) -> type[V]:
        """Get Resources class."""
        if self._resources_class is None:
            self._resources_class = self._extract_resources_class()
        return self._resources_class

    @property
    def dependencies(self) -> dict[str, Dependency]:
        """Get scanned dependencies."""
        if not self._dependencies:
            self._dependencies = self._scan_dependencies()
            self._resolution_order = _make_resolve_order(self._dependencies)
        return self._dependencies

    @property
    def resolution_order(self) -> list[str]:
        """Get dependency resolution order."""
        if not self._resolution_order:
            self._resolution_order = _make_resolve_order(self.dependencies)
        return self._resolution_order

    def _scan_dependencies(self) -> dict[str, Dependency]:
        """Scan class attributes for Dependency descriptors."""
        dependencies = {}
        for name, attr in vars(self.__class__).items():
            if isinstance(attr, Dependency):
                dependencies[name] = attr
        return dependencies

    async def __aenter__(self) -> V:
        if self._stack:
            raise ContainerReuseError(
                "Container instance cannot be reused. Create a new instance for each usage."
            )

        self._stack = AsyncExitStack()
        await self._stack.__aenter__()

        resolved: ResolvedDeps = {}

        for name in self.resolution_order:
            dependency = self.dependencies[name]
            instance = await dependency.resolve(resolved)
            resolved[name] = instance

            if hasattr(dependency.factory, CLEANUP_ATTR_NAME):
                cleanup_getter = getattr(dependency.factory, CLEANUP_ATTR_NAME)
                cleanup = _make_cleanup(cleanup_getter(instance))
                self._stack.push_async_callback(cleanup)

        resources = self.resources_class()
        setattr(resources, "settings", self._settings)

        for name, instance in resolved.items():
            setattr(resources, name, instance)

        return resources

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Cleanup all resources."""
        if self._stack:
            await self._stack.__aexit__(exc_type, exc_val, exc_tb)
            self._stack = None

    def _extract_resources_class(self) -> type[V]:
        """Extract Resources class from AsyncExitStackContainer[T, V] generic."""
        origin_base = _extract_origin_base(self.__class__)
        if _extract_origin(origin_base) is not AsyncExitStackContainer:
            raise InvalidContainerInheritance(
                f"{self.__class__.__name__} must directly inherit from AsyncExitStackContainer[T, V], got {origin_base}."
            )
        return _extract_resource_cls(origin_base)


def _extract_resource_cls[T, V](
    origin_base: type[AsyncExitStackContainer[T, V]],
) -> type[V[T]]:
    if args := getattr(origin_base, "__args__", None):
        if len(args) == 2:
            resources_cls = args[1]
            origin_base = _extract_origin_base(resources_cls)
            origin = _extract_origin(origin_base)
            if origin is BaseResources:
                return resources_cls
    raise InvalidContainerInheritance(
        f"Cannot extract Resources class from {origin_base}: ensure proper generic inheritance from BaseResources."
    )


def _extract_origin_base(cls: type) -> type:
    if orig_bases := getattr(cls, "__orig_bases__", None):
        return orig_bases[0]
    raise InvalidContainerInheritance(
        f"Cannot extract base from {cls.__name__}: __orig_bases__ not found. Ensure proper generic inheritance."
    )


def _extract_origin(cls: type) -> type:
    if origin := getattr(cls, "__origin__", None):
        return origin
    raise InvalidContainerInheritance(
        f"Cannot extract __origin__ from {cls}: not a generic type. Ensure proper generic inheritance."
    )


def _make_resolve_order(dependencies: dict[str, Dependency]) -> list[str]:
    graph: DependencyGraph = {}
    for name, dep in dependencies.items():
        deps = set()
        for value in dep.kwargs.values():
            if isinstance(value, Dependency) and value.name:
                deps.add(value.name)
        graph[name] = deps

    in_degree = {name: len(deps) for name, deps in graph.items()}
    queue = [name for name, degree in in_degree.items() if degree == 0]
    queue.sort()
    ordered_deps = []

    while queue:
        node = queue.pop(0)
        ordered_deps.append(node)

        for name, deps in graph.items():
            if node in deps:
                in_degree[name] -= 1
                if in_degree[name] == 0 and name not in ordered_deps:
                    queue.append(name)

    if len(ordered_deps) != len(graph):
        pending = [name for name, degree in in_degree.items() if degree > 0]
        raise CircularDependencyError(
            f"Cannot resolve dependencies: circular dependency detected (resolved: {ordered_deps}, pending: {pending})"
        )

    return ordered_deps


def _make_cleanup(cleanup_fn: CleanupFn) -> Callable[[], Awaitable[None]]:
    if inspect.iscoroutinefunction(cleanup_fn):
        return cleanup_fn

    async def _wrapper() -> None:
        result = cleanup_fn()
        if inspect.iscoroutine(result):
            await result

    return _wrapper


__all__ = [
    "AsyncExitStackContainer",
]
