"""
Error handling and traceback cleaning utilities (Phase 4)
Provides verify/retry loop, traceback cleaning, and error summarization.
"""

from __future__ import annotations

import re
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ErrorSummary:
    """Structured error summary for retry decisions"""
    error_type: str = ""
    error_message: str = ""
    file_path: str = ""
    line_number: int | None = None
    snippet: str = ""
    suggestion: str = ""
    retry_eligible: bool = False


def clean_traceback(tb_string: str, max_lines: int = 20) -> str:
    """
    Phase 4: Clean traceback to essential info only.
    Remove internal frames, keep user code frames.
    """
    lines = tb_string.strip().split("\n")

    # Filter patterns
    internal_patterns = [
        r"/\.pyenv/",
        r"/usr/local/lib/",
        r"/usr/lib/",
        r"site-packages/",
        r"/opt/homebrew/",
        r"claude-code/",
        r"/var/folders/",
        r"asyncio/",
        r"concurrent/futures",
    ]

    filtered = []
    for line in lines:
        # Skip internal frames
        if any(re.search(p, line) for p in internal_patterns):
            continue
        filtered.append(line)

    # If too long, keep head and tail
    if len(filtered) > max_lines:
        head = filtered[:max_lines // 2]
        tail = filtered[-max_lines // 2:]
        return "\n".join(head + ["\n... (internal frames omitted) ...\n"] + tail)

    return "\n".join(filtered)


def summarize_error(error: Exception, context: dict[str, Any] | None = None) -> ErrorSummary:
    """
    Phase 4: Summarize error for retry decisions.
    Extracts key info without full traceback.
    """
    summary = ErrorSummary()

    # Get error type and message
    summary.error_type = type(error).__name__
    summary.error_message = str(error)

    # Try to extract location from traceback
    tb = traceback.extract_tb(error.__traceback__) if error.__traceback__ else []
    if tb:
        # Find the most relevant frame (usually the last user code frame)
        for frame in reversed(tb):
            file_path = frame.filename
            # Skip internal files
            if "/site-packages/" in file_path or "/.pyenv/" in file_path:
                continue
            summary.file_path = file_path
            summary.line_number = frame.lineno
            summary.snippet = frame.line or ""
            break

    # Determine retry eligibility and suggestion
    if isinstance(error, SyntaxError):
        summary.retry_eligible = True
        summary.suggestion = "Fix syntax error at reported location"
    elif isinstance(error, (ImportError, ModuleNotFoundError)):
        summary.retry_eligible = False
        summary.suggestion = "Check dependencies and imports"
    elif isinstance(error, FileNotFoundError):
        summary.retry_eligible = True
        summary.suggestion = f"Verify file exists: {error.filename if hasattr(error, 'filename') else 'unknown'}"
    elif isinstance(error, PermissionError):
        summary.retry_eligible = False
        summary.suggestion = "Check file permissions"
    elif summary.error_type == "ToolError":
        summary.retry_eligible = True
        summary.suggestion = "Review tool parameters and retry"
    else:
        # Default: allow retry for unknown errors
        summary.retry_eligible = True
        summary.suggestion = "Review error and retry"

    return summary


class RetryLoop:
    """
    Phase 4: Verify/Retry loop controller.
    Manages retry attempts with backoff and error tracking.
    """

    MAX_RETRIES = 3
    BACKOFF_MULTIPLIER = 1.5

    def __init__(self, max_retries: int | None = None):
        self.max_retries = max_retries or self.MAX_RETRIES
        self.attempts: list[ErrorSummary] = []
        self.current_attempt = 0

    def should_retry(self, error: Exception | None = None) -> tuple[bool, str]:
        """
        Determine if we should retry or give up.
        Returns: (should_retry, reason)
        """
        if error is None:
            # No error, check if we've exhausted attempts
            if self.current_attempt >= self.max_retries:
                return False, f"Max retries ({self.max_retries}) reached"
            return True, ""

        # Summarize error
        summary = summarize_error(error)
        self.attempts.append(summary)
        self.current_attempt += 1

        # Check if retry eligible
        if not summary.retry_eligible:
            return False, f"Error not retryable: {summary.suggestion}"

        # Check max retries
        if self.current_attempt >= self.max_retries:
            return False, f"Max retries ({self.max_retries}) reached. Last error: {summary.error_message}"

        return True, f"Attempt {self.current_attempt}/{self.max_retries}: {summary.suggestion}"

    def get_error_history(self) -> str:
        """Get formatted error history for reporting"""
        lines = [f"Error History ({len(self.attempts)} attempts):"]
        for i, summary in enumerate(self.attempts, 1):
            loc = f"{summary.file_path}:{summary.line_number}" if summary.line_number else "unknown"
            lines.append(f"  {i}. [{summary.error_type}] at {loc}")
            lines.append(f"     {summary.error_message[:100]}")
            if summary.suggestion:
                lines.append(f"     Suggestion: {summary.suggestion}")
        return "\n".join(lines)

    def format_for_reanchor(self) -> dict[str, Any]:
        """
        Format error info for Re-anchor decision.
        Returns context needed for re-anchor analysis.
        """
        if not self.attempts:
            return {}

        last = self.attempts[-1]
        return {
            "error_type": last.error_type,
            "file_path": last.file_path,
            "line_number": last.line_number,
            "error_message": last.error_message,
            "total_attempts": self.current_attempt,
            "suggestion": last.suggestion,
        }


def verify_and_retry(
    func,
    *args,
    max_retries: int = 3,
    on_retry: callable | None = None,
    on_give_up: callable | None = None,
    **kwargs
):
    """
    Phase 4: Wrapper for verify/retry loop.

    Example:
        result = verify_and_retry(
            tool.execute,
            file_path="test.py",
            old_string="old",
            new_string="new"
        )
    """
    retry_loop = RetryLoop(max_retries=max_retries)

    while True:
        should_retry, reason = retry_loop.should_retry()
        if not should_retry:
            if on_give_up:
                on_give_up(retry_loop)
            raise RuntimeError(f"Max retries reached. {reason}\n{retry_loop.get_error_history()}")

        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            should_retry, reason = retry_loop.should_retry(e)

            if not should_retry:
                if on_give_up:
                    on_give_up(retry_loop)
                raise RuntimeError(f"Operation failed: {reason}\n{retry_loop.get_error_history()}") from e

            if on_retry:
                context = retry_loop.format_for_reanchor()
                on_retry(retry_loop, context)

            # Continue to next retry
