"""Read-only review packet builder.

Builds a compact review packet from task goal, git metadata, changed files,
and test evidence.  Does not call an LLM and does not perform review.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Protocol

# Paths that should trigger a risk flag if present in changed files
_LOCAL_ARTIFACT_PREFIXES = (
    ".ai-dev/tasks/",
    ".ai-dev/context-packs/",
    ".ai-dev/worklogs/",
    ".ai-dev/checkpoints/",
    ".ai-dev/tmp/",
    ".codegraph/",
    ".codebase-memory/",
)

_MAX_DIFF_LINES_DEFAULT = 50
_MAX_DIFF_BYTES_DEFAULT = 5_000


class GitRunner(Protocol):
    """Protocol for a callable that runs a git sub-command and returns stdout."""

    def __call__(self, args: list[str]) -> str:
        ...


@dataclass
class ReviewPacket:
    """Compact review packet ready for human or LLM consumption."""

    task_goal: str
    changed_files: list[str] = field(default_factory=list)
    diff_stat: str = ""
    focused_diffs: dict[str, str] = field(default_factory=dict)
    test_summary: str | None = None
    truncated: bool = False
    local_artifact_flags: list[str] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)


def _run_git(git_runner: GitRunner | Callable[[list[str]], str], args: list[str]) -> str:
    """Invoke *git_runner* and return stripped stdout, or empty string on failure."""
    try:
        return git_runner(args).strip()
    except Exception:
        return ""


def _run_git_raw(git_runner: GitRunner | Callable[[list[str]], str], args: list[str]) -> str:
    """Invoke *git_runner* and return raw stdout, or empty string on failure."""
    try:
        return git_runner(args)
    except Exception:
        return ""


def _changed_files_from_stat(diff_stat: str) -> list[str]:
    """Parse ``git diff --stat`` output for file names."""
    files: list[str] = []
    for line in diff_stat.splitlines():
        line = line.rstrip()
        if not line:
            continue
        # Typical line: " src/core/review_packet.py | 12 +---"
        # Summary lines (e.g. " 2 files changed...") do not contain " | ".
        parts = line.split(" | ", 1)
        if len(parts) == 2:
            files.append(parts[0].strip())
    return files


def _changed_files_from_status(status_output: str) -> list[str]:
    """Parse ``git status --short`` output for file names."""
    files: list[str] = []
    for line in status_output.splitlines():
        line = line.rstrip()
        if not line:
            continue
        # Format: "XY filename" or "XY old -> new" (X/Y are status chars).
        payload = line[3:] if len(line) > 3 else line
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1]
        files.append(payload.strip())
    return files


def _is_local_artifact_path(path: str) -> bool:
    """Return True if *path* lives under a known local-artifact directory."""
    norm = path.replace("\\", "/")
    return any(norm.startswith(prefix) or ("/" + prefix) in norm for prefix in _LOCAL_ARTIFACT_PREFIXES)


def _truncate_diff(diff: str, *, max_lines: int, max_bytes: int) -> tuple[str, bool]:
    """Return (possibly truncated diff, was_truncated)."""
    encoded = diff.encode("utf-8")
    if len(encoded) <= max_bytes and diff.count("\n") <= max_lines:
        return diff, False

    lines = diff.splitlines(keepends=True)
    truncated_lines: list[str] = []
    current_bytes = 0
    for i, line in enumerate(lines):
        line_bytes = line.encode("utf-8")
        if i >= max_lines or current_bytes + len(line_bytes) > max_bytes:
            return "".join(truncated_lines) + "... [truncated]\n", True
        truncated_lines.append(line)
        current_bytes += len(line_bytes)

    return "".join(truncated_lines), False


def build_review_packet(
    task_goal: str,
    git_runner: GitRunner | Callable[[list[str]], str],
    *,
    test_summary: str | None = None,
    max_diff_lines: int = _MAX_DIFF_LINES_DEFAULT,
    max_diff_bytes: int = _MAX_DIFF_BYTES_DEFAULT,
    include_diff: bool = False,
) -> ReviewPacket:
    """Build a compact :class:`ReviewPacket`.

    Parameters
    ----------
    task_goal:
        Short description of what the task aimed to accomplish.
    git_runner:
        Callable that receives a list of git arguments (e.g. ``["diff", "--stat"]``)
        and returns the command's stdout as a string.
    test_summary:
        Optional free-form summary of test results.
    max_diff_lines:
        Maximum number of diff lines to include per focused diff.
    max_diff_bytes:
        Maximum number of bytes to include per focused diff.
    include_diff:
        When False (default) only the diff stat and changed-file list are collected.
        When True, a focused diff per changed file is also gathered and truncated
        if necessary.
    """
    diff_stat = _run_git(git_runner, ["diff", "--stat"])
    changed_files = _changed_files_from_stat(diff_stat)

    # Fallback to status when diff --stat is empty (e.g. staged-only changes)
    if not changed_files:
        status = _run_git(git_runner, ["status", "--short"])
        changed_files = _changed_files_from_status(status)

    packet = ReviewPacket(
        task_goal=task_goal,
        changed_files=changed_files,
        diff_stat=diff_stat,
        test_summary=test_summary,
    )

    # Flag local artifact paths
    for path in changed_files:
        if _is_local_artifact_path(path):
            packet.local_artifact_flags.append(path)

    if packet.local_artifact_flags:
        packet.risk_notes.append(
            "Changed files include local artifact paths that should not be committed."
        )

    # Gather focused diffs when requested
    if include_diff and changed_files:
        for path in changed_files:
            raw = _run_git_raw(git_runner, ["diff", "--", path])
            if not raw:
                raw = _run_git_raw(git_runner, ["diff", "--staged", "--", path])
            if raw:
                trimmed, was_trunc = _truncate_diff(
                    raw, max_lines=max_diff_lines, max_bytes=max_diff_bytes
                )
                packet.focused_diffs[path] = trimmed
                if was_trunc:
                    packet.truncated = True

    return packet
