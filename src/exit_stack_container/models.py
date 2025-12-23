"""DI container with async lifecycle management."""

from __future__ import annotations

from msgspec_settings import BaseSettings


class BaseResources[T = BaseSettings]:
    """Base DTO for container resources."""

    settings: T


__all__ = [
    "BaseResources",
]
