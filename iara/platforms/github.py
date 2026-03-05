"""GitHub platform adapter for posting code review comments."""

import logging
import requests
from typing import List, Dict, Any
from .base import PlatformAdapter


logger = logging.getLogger(__name__)


class GitHubAdapter(PlatformAdapter):
    """GitHub-specific adapter for posting review comments.

    Uses GitHub's Pull Request Review Comments API for inline comments
    and Issues Comments API for summary comments.
    """

    def __init__(self, token: str, repo: str, pr_id: str):
        """Initialize GitHub adapter.

        Args:
            token: GitHub personal access token or GITHUB_TOKEN
            repo: Repository in format 'owner/repo'
            pr_id: Pull request number
        """
        super().__init__(token, repo, pr_id)
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }

    def post_inline_comments(
        self,
        commit_sha: str,
        comments: List[Dict[str, Any]]
    ) -> bool:
        """Post inline review comments using GitHub PR Review API.

        Args:
            commit_sha: Git commit SHA to anchor comments to
            comments: List of comment dictionaries with keys:
                - file: str - relative file path
                - line: int - line number in the new file
                - severity: str - bug, security, performance, style, other
                - message: str - comment text with emoji prefix

        Returns:
            True if review posted successfully, False otherwise
        """
        if not comments:
            logger.warning("No comments to post (empty list)")
            return True

        # Format comments for GitHub PR Review API
        gh_comments = []
        for comment in comments:
            gh_comments.append({
                "path": comment["file"],
                "line": comment["line"],
                "body": comment["message"]
            })

        # Prepare payload for PR Review API
        payload = {
            "commit_id": commit_sha,
            "event": "COMMENT",
            "comments": gh_comments
        }

        # POST to GitHub PR Review API
        url = f"{self.base_url}/repos/{self.repo}/pulls/{self.pr_id}/reviews"

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=30
            )

            if response.status_code in (200, 201):
                logger.info(
                    f"Successfully posted {len(gh_comments)} inline comments "
                    f"to PR #{self.pr_id}"
                )
                return True
            else:
                logger.error(
                    f"Failed to post inline comments (HTTP {response.status_code}): "
                    f"{response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting inline comments to GitHub: {e}")
            return False

    def post_summary_comment(self, body: str) -> bool:
        """Post a single summary comment using GitHub Issues API.

        Args:
            body: Markdown-formatted comment body

        Returns:
            True if comment posted successfully, False otherwise
        """
        # Add Iara header and footer
        comment_body = f"""## 🧜‍♀️ Iara Code Review

{body}

---
*Reviewed by [Iara](https://github.com/felipefernandes/iara) - AI Code Reviewer*"""

        payload = {"body": comment_body}

        # POST to GitHub Issues Comments API
        url = f"{self.base_url}/repos/{self.repo}/issues/{self.pr_id}/comments"

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=30
            )

            if response.status_code in (200, 201):
                logger.info(f"Successfully posted summary comment to PR #{self.pr_id}")
                return True
            else:
                logger.error(
                    f"Failed to post summary comment (HTTP {response.status_code}): "
                    f"{response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting summary comment to GitHub: {e}")
            return False
