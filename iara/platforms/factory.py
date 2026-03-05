"""Platform adapter factory for creating platform-specific adapters."""

import logging
from typing import Optional
from .base import PlatformAdapter
from .github import GitHubAdapter
from .gitlab import GitLabAdapter


logger = logging.getLogger(__name__)


def get_adapter(
    platform: Optional[str],
    token: str,
    repo: str,
    pr_id: str,
    **kwargs
) -> PlatformAdapter:
    """Create and return the appropriate platform adapter.

    Args:
        platform: Platform name ('github' or 'gitlab')
        token: API authentication token
        repo: Repository identifier (format depends on platform)
        pr_id: Pull/Merge request identifier
        **kwargs: Additional platform-specific parameters
            - For GitLab: base_sha, head_sha (optional)

    Returns:
        PlatformAdapter instance for the specified platform

    Raises:
        ValueError: If platform is not supported or None
    """
    if platform is None:
        raise ValueError(
            "Platform not specified. Set ci.platform in .iara.json to 'github' or 'gitlab'"
        )

    platform_lower = platform.lower()

    if platform_lower == "github":
        logger.info("Using GitHub adapter for comment posting")
        return GitHubAdapter(token, repo, pr_id)

    elif platform_lower == "gitlab":
        logger.info("Using GitLab adapter for comment posting")
        # Extract GitLab-specific parameters
        base_sha = kwargs.get("base_sha")
        head_sha = kwargs.get("head_sha")
        return GitLabAdapter(token, repo, pr_id, base_sha, head_sha)

    else:
        raise ValueError(
            f"Unsupported platform: '{platform}'. "
            f"Supported platforms: github, gitlab"
        )
