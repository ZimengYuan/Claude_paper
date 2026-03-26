"""Shared application services for CLI, MCP, and Web entry points."""

from .common import ServiceError, resolve_paper_dir

__all__ = [
    "ServiceError",
    "resolve_paper_dir",
]
