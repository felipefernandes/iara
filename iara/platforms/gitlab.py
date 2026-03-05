"""GitLab platform adapter for posting code review comments."""

import logging
import requests
from typing import List, Dict, Any
from .base import PlatformAdapter


logger = logging.getLogger(__name__)


class GitLabAdapter(PlatformAdapter):
    """GitLab-specific adapter for posting review comments.

    Uses GitLab's Merge Request Discussions API for inline comments
    and Merge Request Notes API for summary comments.
    """

    def __init__(self, token: str, repo: str, pr_id: str, base_sha: str = None, head_sha: str = None):
        """Initialize GitLab adapter.

        Args:
            token: GitLab personal access token or CI_JOB_TOKEN
            repo: Project ID (can be numeric ID or 'namespace/project' URL-encoded)
            pr_id: Merge request IID (internal ID)
            base_sha: Base commit SHA (target branch HEAD)
            head_sha: Head commit SHA (source branch HEAD)
        """
        super().__init__(token, repo, pr_id)
        self.base_sha = base_sha
        self.head_sha = head_sha
        self.base_url = "https://gitlab.com/api/v4"
        self.headers = {
            "PRIVATE-TOKEN": token,
            "Content-Type": "application/json"
        }

    def post_inline_comments(
        self,
        commit_sha: str,
        comments: List[Dict[str, Any]]
    ) -> bool:
        """Post inline review comments using GitLab MR Discussions API.

        Note: GitLab requires individual API calls for each discussion.

        Args:
            commit_sha: Git commit SHA to anchor comments to (used as head_sha)
            comments: List of comment dictionaries with keys:
                - file: str - relative file path
                - line: int - line number in the new file
                - severity: str - bug, security, performance, style, other
                - message: str - comment text with emoji prefix

        Returns:
            True if all discussions posted successfully, False otherwise
        """
        if not comments:
            logger.warning("No comments to post (empty list)")
            return True

        # Use provided head_sha or fall back to commit_sha
        head_sha = self.head_sha or commit_sha
        base_sha = self.base_sha or commit_sha  # Fallback to same SHA if not provided

        success_count = 0
        failed_count = 0

        # POST individual discussions (GitLab doesn't have batch API like GitHub)
        url = f"{self.base_url}/projects/{self.repo}/merge_requests/{self.pr_id}/discussions"

        for comment in comments:
            payload = {
                "body": comment["message"],
                "position": {
                    "base_sha": base_sha,
                    "start_sha": base_sha,
                    "head_sha": head_sha,
                    "position_type": "text",
                    "new_path": comment["file"],
                    "new_line": comment["line"]
                }
            }

            try:
                response = requests.post(
                    url,
                    json=payload,
                    headers=self.headers,
                    timeout=30
                )

                if response.status_code in (200, 201):
                    success_count += 1
                else:
                    failed_count += 1
                    logger.error(
                        f"Failed to post inline comment on {comment['file']}:{comment['line']} "
                        f"(HTTP {response.status_code}): {response.text}"
                    )

            except requests.exceptions.RequestException as e:
                failed_count += 1
                logger.error(
                    f"Error posting inline comment on {comment['file']}:{comment['line']}: {e}"
                )

        logger.info(
            f"Posted {success_count}/{len(comments)} inline comments to MR !{self.pr_id} "
            f"({failed_count} failed)"
        )

        # Return True only if all comments posted successfully
        return failed_count == 0

    def post_summary_comment(self, body: str) -> bool:
        """Post a single summary comment using GitLab MR Notes API.

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

        # POST to GitLab MR Notes API
        url = f"{self.base_url}/projects/{self.repo}/merge_requests/{self.pr_id}/notes"

        try:
            response = requests.post(
                url,
                json=payload,
                headers=self.headers,
                timeout=30
            )

            if response.status_code in (200, 201):
                logger.info(f"Successfully posted summary comment to MR !{self.pr_id}")
                return True
            else:
                logger.error(
                    f"Failed to post summary comment (HTTP {response.status_code}): "
                    f"{response.text}"
                )
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Error posting summary comment to GitLab: {e}")
            return False
