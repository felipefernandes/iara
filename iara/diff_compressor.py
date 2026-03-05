"""Intelligent diff compression to handle large pull request diffs."""

import re
import sys
import logging

logger = logging.getLogger(__name__)


class DiffCompressor:
    """
    Compresses diffs by removing context lines when necessary.
    Preserves file headers, hunks, and all added/removed lines.
    """

    def __init__(self, max_diff_tokens: int = 12000):
        """
        Initialize the diff compressor.

        Args:
            max_diff_tokens: Maximum number of characters allowed in the diff

        Raises:
            ValueError: If max_diff_tokens is not a positive integer
        """
        # Validate and convert max_diff_tokens to int
        try:
            max_diff_tokens = int(max_diff_tokens)
        except (TypeError, ValueError):
            raise ValueError(
                f"max_diff_tokens must be a positive integer, got {type(max_diff_tokens).__name__}"
            )

        if max_diff_tokens <= 0:
            raise ValueError(f"max_diff_tokens must be positive, got {max_diff_tokens}")

        self.max_diff_tokens = max_diff_tokens

    def compress(self, diff: str) -> str:
        """
        Compress a diff string if it exceeds the token limit.

        Args:
            diff: The raw diff string

        Returns:
            Compressed diff string (or original if under limit)
        """
        original_size = len(diff)

        # If diff is under the limit, return as-is
        if original_size <= self.max_diff_tokens:
            return diff

        # Parse diff into individual file blocks
        files = self._parse_diff_files(diff)

        # Compress by removing context lines
        compressed_diff = self._prioritize_and_compress(files)

        compressed_size = len(compressed_diff)
        reduction_pct = int((1 - compressed_size / original_size) * 100) if original_size > 0 else 0

        # Log compression statistics
        msg = (
            f"🗜️  Diff compressed: {self._format_size(original_size)} → "
            f"{self._format_size(compressed_size)} ({reduction_pct}% reduction)"
        )
        logger.info(msg)
        print(msg, file=sys.stderr)

        return compressed_diff

    def _parse_diff_files(self, diff: str):
        """
        Parse the diff into individual file changes.

        Args:
            diff: The raw diff string

        Returns:
            List of tuples (file_header, hunks) for each file
        """
        files = []

        # Find all "diff --git" markers and their positions
        matches = list(re.finditer(r'^diff --git .+$', diff, re.MULTILINE))

        if not matches:
            # No diff markers found, return empty list
            return files

        for i, match in enumerate(matches):
            # Extract the header line
            header = match.group(0)

            # Determine content: from end of this header to start of next header (or EOF)
            start_pos = match.end() + 1  # +1 to skip the newline after header
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(diff)

            # Extract content between this header and the next
            content = diff[start_pos:end_pos].rstrip('\n')

            files.append((header, content))

        return files

    def _prioritize_and_compress(self, files):
        """
        Compress files by stripping context lines while preserving structure.

        Args:
            files: List of (header, content) tuples

        Returns:
            Compressed diff string
        """
        result_parts = []

        for header, content in files:
            # Start with the file header
            file_parts = [header]

            # Split content into lines
            lines = content.split('\n')

            # Process each line
            for line in lines:
                # Always keep file metadata (---, +++, @@)
                if line.startswith('---') or line.startswith('+++') or line.startswith('@@'):
                    file_parts.append(line)
                # Keep added lines
                elif line.startswith('+'):
                    file_parts.append(line)
                # Keep removed lines
                elif line.startswith('-'):
                    file_parts.append(line)
                # Skip context lines (lines starting with space or blank)
                # This is where compression happens

            result_parts.append('\n'.join(file_parts))

        # Join all files back together
        compressed = '\n'.join(result_parts)

        # If still too large, truncate with a warning
        if len(compressed) > self.max_diff_tokens:
            compressed = compressed[:self.max_diff_tokens]
            compressed += "\n\n[... diff still too large, truncated ...]"

        return compressed

    def _format_size(self, size_bytes: int) -> str:
        """
        Format byte size as KB with one decimal place.

        Args:
            size_bytes: Size in bytes (characters)

        Returns:
            Formatted string like "30.5KB"
        """
        kb = size_bytes / 1024
        return f"{kb:.1f}KB"
