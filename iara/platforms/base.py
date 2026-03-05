"""Base platform adapter interface for posting code review comments."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class PlatformAdapter(ABC):
    """Abstract base class for platform-specific comment posting adapters.

    Implementations provide platform-specific logic for posting review comments
    to different CI/CD platforms (GitHub, GitLab, etc.).
    """

    def __init__(self, token: str, repo: str, pr_id: str):
        """Initialize the platform adapter.

        Args:
            token: API authentication token
            repo: Repository identifier (format depends on platform)
            pr_id: Pull/Merge request identifier
        """
        self.token = token
        self.repo = repo
        self.pr_id = pr_id

    @abstractmethod
    def post_inline_comments(
        self,
        commit_sha: str,
        comments: List[Dict[str, Any]]
    ) -> bool:
        """Post inline comments on specific lines of code.

        Args:
            commit_sha: Git commit SHA to anchor comments to
            comments: List of comment dictionaries with keys:
                - file: str - relative file path
                - line: int - line number in the new file
                - severity: str - one of: bug, security, performance, style, other
                - message: str - comment text with emoji prefix

        Returns:
            True if all comments posted successfully, False otherwise
        """
        raise NotImplementedError

    @abstractmethod
    def post_summary_comment(self, body: str) -> bool:
        """Post a single summary comment on the PR/MR.

        Used as the primary mode when review_mode is 'summary',
        or as a fallback when inline posting fails.

        Args:
            body: Markdown-formatted comment body

        Returns:
            True if comment posted successfully, False otherwise
        """
        raise NotImplementedError
