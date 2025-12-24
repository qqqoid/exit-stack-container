"""DI container with async lifecycle management."""

from __future__ import annotations

from contextlib import AsyncExitStack
from typing import Any

from exit_stack_container.container.helpers import make_cleanup

from ..defaults import CLEANUP_ATTR_NAME
from ..exceptions import ContainerReuseError
from ..types import ResolvedDeps
from .container import AbstractContainer


class AsyncExitStackContainer[T, V](AbstractContainer[T, V]):
    """DI container with async lifecycle management."""

    _settings: T
    _stack: AsyncExitStack | None = None

    async def __aenter__(self) -> V:
        if self._stack:
            raise ContainerReuseError("This container instance has already been entered and cannot be reused before exiting.")

        self._stack = AsyncExitStack()
        await self._stack.__aenter__()

        resolved: ResolvedDeps = {}

        for name in self.resolution_order:
            dependency = self.dependencies[name]
            instance = await dependency.resolve(resolved)
            resolved[name] = instance

            if hasattr(dependency.factory, CLEANUP_ATTR_NAME):
                cleanup_getter = getattr(dependency.factory, CLEANUP_ATTR_NAME)
                cleanup = make_cleanup(cleanup_getter(instance))
                self._stack.push_async_callback(cleanup)

        resources = self.resources_class()
        setattr(resources, "settings", self._settings)

        for name, instance in resolved.items():
            setattr(resources, name, instance)

        return resources

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context, cleaning up resources."""
        if self._stack:
            await self._stack.__aexit__(exc_type, exc_val, exc_tb)
            self._stack = None
