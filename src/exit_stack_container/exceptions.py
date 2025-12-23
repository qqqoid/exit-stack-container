"""Exceptions for container module."""


class ContainerError(Exception):
    """Base exception for container errors."""


class CircularDependencyError(ContainerError):
    """Raised when circular dependency detected in container."""


class DependencyNotResolvedError(ContainerError):
    """Raised when dependency is not yet resolved."""


class ContainerReuseError(ContainerError):
    """Raised when attempting to reuse container instance."""


class InvalidContainerInheritance(ContainerError):
    """Raised when container inheritance structure is invalid."""


__all__ = [
    "ContainerError",
    "CircularDependencyError",
    "DependencyNotResolvedError",
    "ContainerReuseError",
    "InvalidContainerInheritance",
]
