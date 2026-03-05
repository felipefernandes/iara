"""Post code review comments using platform adapters."""

import sys
import logging
import os
from iara.config import load_config
from iara.parsers.inline_parser import parse_inline_review
from iara.platforms.factory import get_adapter


logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def post_review_comments(review_text: str) -> int:
    """Post review comments using configured platform adapter.

    Args:
        review_text: Review output from LLM (JSON for inline mode, markdown for summary)

    Returns:
        0 on success, 1 on error
    """
    try:
        # Load configuration
        config = load_config()
        ci_config = config.get("ci", {})
        platform = ci_config.get("platform")
        review_mode = ci_config.get("review_mode", "summary")

        # Get required environment variables
        token = os.environ.get("GITHUB_TOKEN")
        repo = os.environ.get("REPO")
        pr_number = os.environ.get("PR_NUMBER")
        commit_sha = os.environ.get("HEAD_SHA") or os.environ.get("GITHUB_SHA")

        if not token:
            logger.error("GITHUB_TOKEN environment variable not set")
            return 1

        if not repo:
            logger.error("REPO environment variable not set")
            return 1

        if not pr_number:
            logger.error("PR_NUMBER environment variable not set")
            return 1

        # Summary mode (default) - always use platform adapter if configured
        if review_mode == "summary" or platform is None:
            if platform is None:
                logger.info("No platform configured, using summary mode")
                # For now, just output the review (run_iara.sh will handle posting)
                print(review_text)
                return 0

            logger.info(f"Posting summary comment in {review_mode} mode")
            adapter = get_adapter(platform, token, repo, pr_number)
            success = adapter.post_summary_comment(review_text)

            if success:
                logger.info("Summary comment posted successfully")
                return 0
            else:
                logger.error("Failed to post summary comment")
                return 1

        # Inline mode - try to parse JSON and post inline comments
        elif review_mode == "inline":
            if not commit_sha:
                logger.error("HEAD_SHA or GITHUB_SHA environment variable not set (required for inline mode)")
                return 1

            logger.info("Attempting to post inline comments")

            try:
                # Parse JSON output
                data = parse_inline_review(review_text)
                comments = data["comments"]
                summary = data["summary"]

                logger.info(f"Parsed {len(comments)} inline comments")

                # Get platform adapter
                adapter = get_adapter(platform, token, repo, pr_number, head_sha=commit_sha)

                # Try to post inline comments
                if comments:
                    success = adapter.post_inline_comments(commit_sha, comments)

                    if success:
                        logger.info(f"Successfully posted {len(comments)} inline comments")
                        # Also post a summary comment with overview
                        adapter.post_summary_comment(summary)
                        return 0
                    else:
                        logger.warning("Inline comment posting failed, falling back to summary mode")
                        # Fallback: format as summary with line numbers
                        fallback_text = format_inline_as_summary(data)
                        adapter.post_summary_comment(fallback_text)
                        return 0
                else:
                    # No issues found - post summary only
                    logger.info("No inline comments to post, posting summary only")
                    adapter.post_summary_comment(summary)
                    return 0

            except ValueError as e:
                # JSON parse error - fallback to summary mode
                logger.warning(f"Failed to parse inline review JSON: {e}")
                logger.warning("Falling back to summary mode")

                adapter = get_adapter(platform, token, repo, pr_number)
                fallback_text = f"""**Note**: Inline mode failed (invalid JSON response from LLM)

{review_text}"""
                adapter.post_summary_comment(fallback_text)
                return 0

            except Exception as e:
                # Other error - fallback to summary mode
                logger.error(f"Error in inline mode: {e}")
                logger.warning("Falling back to summary mode")

                adapter = get_adapter(platform, token, repo, pr_number)
                adapter.post_summary_comment(review_text)
                return 0

        else:
            logger.error(f"Invalid review_mode: {review_mode}")
            return 1

    except Exception as e:
        logger.error(f"Fatal error posting comments: {e}", exc_info=True)
        return 1


def format_inline_as_summary(data: dict) -> str:
    """Format inline review data as a summary comment with line numbers.

    Args:
        data: Parsed inline review data with 'summary' and 'comments' keys

    Returns:
        Formatted markdown text
    """
    summary = data.get("summary", "Code Review")
    comments = data.get("comments", [])

    if not comments:
        return summary

    lines = [summary, "", "---", ""]

    for comment in comments:
        file_path = comment.get("file", "unknown")
        line = comment.get("line", 0)
        message = comment.get("message", "")
        lines.append(f"**{file_path}:{line}**")
        lines.append(message)
        lines.append("")

    return "\n".join(lines)


def main():
    """CLI entry point for posting comments."""
    if len(sys.argv) < 2:
        print("Usage: python -m iara.post_comment <review_text>", file=sys.stderr)
        print("   or: echo '<review_text>' | python -m iara.post_comment -", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "-":
        # Read from stdin
        review_text = sys.stdin.read()
    else:
        # Read from command line argument
        review_text = sys.argv[1]

    exit_code = post_review_comments(review_text)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
