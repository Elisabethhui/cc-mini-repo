from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


DEFAULT_TIMEOUT_SECONDS = 2.0
DEFAULT_MAX_PATHS = 12
DEFAULT_MAX_SUGGESTIONS = 6


@dataclass(frozen=True)
class GitCommandResult:
    returncode: int
    stdout: str
    stderr: str = ""


@dataclass(frozen=True)
class RollbackSuggestion:
    category: str
    command: str
    reason: str


@dataclass(frozen=True)
class RollbackReport:
    git_available: bool
    unstaged_paths: tuple[str, ...]
    staged_paths: tuple[str, ...]
    head_commit: str | None
    suggestions: tuple[RollbackSuggestion, ...]
    warnings: tuple[str, ...]
    truncated: bool = False


def collect_rollback_report(
    root: Path,
    *,
    git_runner: object | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> RollbackReport:
    root = root.resolve()
    runner = git_runner or _run_git
    warnings: list[str] = []
    suggestions: list[RollbackSuggestion] = []
    truncated = False

    status_result = _safe_git(runner, root, ["status", "--short"], timeout_seconds=timeout_seconds)
    if status_result is None:
        return RollbackReport(
            git_available=False,
            unstaged_paths=(),
            staged_paths=(),
            head_commit=None,
            suggestions=(),
            warnings=("git status unavailable",),
            truncated=False,
        )

    unstaged_paths, staged_paths, paths_truncated = _parse_status_lines(status_result.stdout.splitlines())
    truncated = truncated or paths_truncated

    head_result = _safe_git(runner, root, ["rev-parse", "--verify", "HEAD"], timeout_seconds=timeout_seconds)
    head_commit = None
    if head_result is None:
        warnings.append("head commit unavailable")
    else:
        head_commit = head_result.stdout.strip() or None

    if unstaged_paths:
        joined = " ".join(unstaged_paths)
        suggestions.append(
            RollbackSuggestion(
                category="unstaged",
                command=f"git restore -- {joined}",
                reason="discard only unstaged working tree changes",
            )
        )
    if staged_paths:
        joined = " ".join(staged_paths)
        suggestions.append(
            RollbackSuggestion(
                category="staged",
                command=f"git restore --staged -- {joined}",
                reason="unstage changes before deciding whether to discard or edit them",
            )
        )
        suggestions.append(
            RollbackSuggestion(
                category="staged",
                command=f"git restore --worktree -- {joined}",
                reason="discard working tree changes after unstage if you want a full rollback",
            )
        )
    if head_commit is not None:
        short_head = head_commit[:12]
        suggestions.append(
            RollbackSuggestion(
                category="committed",
                command=f"git revert {short_head}",
                reason="create a new commit that safely rolls back an already committed change",
            )
        )
    else:
        warnings.append("cannot suggest committed rollback without a resolved HEAD commit")

    if not unstaged_paths and not staged_paths:
        warnings.append("worktree is clean; committed rollback may be the only relevant option")

    if len(suggestions) > DEFAULT_MAX_SUGGESTIONS:
        suggestions = suggestions[:DEFAULT_MAX_SUGGESTIONS]
        truncated = True

    return RollbackReport(
        git_available=True,
        unstaged_paths=unstaged_paths,
        staged_paths=staged_paths,
        head_commit=head_commit,
        suggestions=tuple(suggestions),
        warnings=tuple(warnings),
        truncated=truncated,
    )


def format_rollback_report(report: RollbackReport) -> str:
    lines = [
        "Rollback Helper",
        f"Git available: {'yes' if report.git_available else 'no'}",
        f"Unstaged paths: {len(report.unstaged_paths)}",
        f"Staged paths: {len(report.staged_paths)}",
        f"Head commit: {report.head_commit[:12] if report.head_commit else '(none)'}",
        "",
        "Suggestions:",
    ]
    if report.suggestions:
        lines.extend(
            f"- {item.command} [{item.category}: {item.reason}]"
            for item in report.suggestions
        )
    else:
        lines.append("- (none)")
    if report.warnings:
        lines.extend(("", "Warnings:"))
        lines.extend(f"- {warning}" for warning in report.warnings)
    if report.truncated:
        lines.extend(("", "Truncated: true"))
    return "\n".join(lines).rstrip()


def _run_git(root: Path, args: list[str], timeout_seconds: float) -> GitCommandResult:
    proc = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout_seconds,
    )
    return GitCommandResult(
        returncode=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def _safe_git(
    runner: object,
    root: Path,
    args: list[str],
    *,
    timeout_seconds: float,
) -> GitCommandResult | None:
    try:
        result = runner(root, args, timeout_seconds)  # type: ignore[misc]
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0:
        return None
    return result


def _parse_status_lines(lines: list[str]) -> tuple[tuple[str, ...], tuple[str, ...], bool]:
    unstaged: list[str] = []
    staged: list[str] = []
    seen_unstaged: set[str] = set()
    seen_staged: set[str] = set()
    truncated = False

    for line in lines:
        if not line.strip():
            continue
        path = _extract_path(line)
        staged_flag = line[0] if line else " "
        unstaged_flag = line[1] if len(line) > 1 else " "

        if unstaged_flag not in {" ", "?"} and path not in seen_unstaged:
            seen_unstaged.add(path)
            unstaged.append(path)
        if staged_flag not in {" ", "?"} and path not in seen_staged:
            seen_staged.add(path)
            staged.append(path)
        if len(unstaged) > DEFAULT_MAX_PATHS:
            unstaged = unstaged[:DEFAULT_MAX_PATHS]
            truncated = True
        if len(staged) > DEFAULT_MAX_PATHS:
            staged = staged[:DEFAULT_MAX_PATHS]
            truncated = True
    return tuple(unstaged), tuple(staged), truncated


def _extract_path(entry: str) -> str:
    payload = entry[3:] if len(entry) > 3 else entry
    if " -> " in payload:
        return payload.split(" -> ", 1)[1].strip()
    return payload.strip()
