"""Type aliases for container module."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any, TypeAlias

# Factory that creates resources (sync or async)
ResourceFactory: TypeAlias = Callable[..., Any]

# Cleanup function (sync or async)
CleanupFn: TypeAlias = Callable[[], None] | Callable[[], Awaitable[None]]

# Extracts cleanup method from resource instance
CleanupGetter: TypeAlias = Callable[[Any], CleanupFn]

# Resolved dependencies mapping
ResolvedDeps: TypeAlias = dict[str, Any]

# Dependency graph for topological sort
DependencyGraph: TypeAlias = dict[str, set[str]]

__all__ = [
    "ResourceFactory",
    "CleanupFn",
    "CleanupGetter",
    "ResolvedDeps",
    "DependencyGraph",
]
