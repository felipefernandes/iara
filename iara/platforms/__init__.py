"""Platform adapters for posting code review comments to different CI platforms."""

from .base import PlatformAdapter
from .github import GitHubAdapter
from .gitlab import GitLabAdapter
from .factory import get_adapter

__all__ = ["PlatformAdapter", "GitHubAdapter", "GitLabAdapter", "get_adapter"]
