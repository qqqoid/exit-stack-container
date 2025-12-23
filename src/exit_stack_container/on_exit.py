"""DI container with async lifecycle management."""

from __future__ import annotations

from typing import Callable

from .defaults import CLEANUP_ATTR_NAME
from .types import CleanupGetter, ResourceFactory


def on_exit(cleanup_getter: CleanupGetter) -> Callable[[ResourceFactory], ResourceFactory]:
    """Register cleanup callback for factory.

    Args:
        cleanup_getter: Extracts cleanup method from instance (e.g., lambda c: c.close)

    Returns:
        Decorated factory
    """

    def decorator(factory: ResourceFactory) -> ResourceFactory:
        setattr(factory, CLEANUP_ATTR_NAME, cleanup_getter)
        return factory

    return decorator


__all__ = [
    "on_exit",
]
