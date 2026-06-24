from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess

from .workflow_status import IGNORED_LOCAL_PATHS


DEFAULT_TIMEOUT_SECONDS = 2.0
DEFAULT_MAX_CHANGED_FILES = 12
DEFAULT_MAX_DIFF_CHARS = 1200
DEFAULT_MAX_SUMMARY_CHARS = 400
DEFAULT_MAX_WARNINGS = 6
DEFAULT_MAX_RISKS = 6


@dataclass(frozen=True)
class GitCommandResult:
    returncode: int
    stdout: str
    stderr: str = ""


@dataclass(frozen=True)
class ReviewPacket:
    task_goal: str
    changed_files: tuple[str, ...]
    diff_stat: tuple[str, ...]
    test_summary: str
    focused_diff: str
    warnings: tuple[str, ...]
    risks: tuple[str, ...]
    truncated: bool = False


def build_review_packet(
    root: Path,
    *,
    task_goal: str,
    test_summary: str,
    focus_files: list[str] | tuple[str, ...] = (),
    git_runner: object | None = None,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    max_changed_files: int = DEFAULT_MAX_CHANGED_FILES,
    max_diff_chars: int = DEFAULT_MAX_DIFF_CHARS,
) -> ReviewPacket:
    root = root.resolve()
    runner = git_runner or _run_git
    warnings: list[str] = []
    risks: list[str] = []
    truncated = False

    status_result = _safe_git(
        runner,
        root,
        ["status", "--short"],
        timeout_seconds=timeout_seconds,
    )
    status_lines = _split_nonempty_lines(status_result.stdout if status_result else "")
    changed_files = _extract_changed_files(status_lines)
    if len(changed_files) > max_changed_files:
        changed_files = changed_files[:max_changed_files]
        truncated = True

    diff_stat_result = _safe_git(
        runner,
        root,
        ["diff", "--stat"],
        timeout_seconds=timeout_seconds,
    )
    diff_stat = _split_nonempty_lines(diff_stat_result.stdout if diff_stat_result else "")

    target_files = tuple(focus_files) if focus_files else changed_files
    focused_diff = ""
    if target_files:
        diff_result = _safe_git(
            runner,
            root,
            ["diff", "--unified=0", "--no-ext-diff", "--", *target_files],
            timeout_seconds=timeout_seconds,
        )
        if diff_result is not None:
            focused_diff, diff_truncated = _truncate_text(diff_result.stdout, max_chars=max_diff_chars)
            truncated = truncated or diff_truncated

    if status_result is None:
        warnings.append("git status unavailable")
    if diff_stat_result is None:
        warnings.append("git diff --stat unavailable")
    elif not diff_stat:
        warnings.append("diff stat is empty")
    if not changed_files:
        warnings.append("no changed files detected")

    risks.extend(_local_artifact_risks(status_lines))
    if focused_diff:
        risks.extend(_sensitive_diff_risks(focused_diff))

    compact_goal, goal_truncated = _truncate_text(task_goal.strip(), max_chars=DEFAULT_MAX_SUMMARY_CHARS)
    compact_test_summary, test_truncated = _truncate_text(test_summary.strip(), max_chars=DEFAULT_MAX_SUMMARY_CHARS)
    truncated = truncated or goal_truncated or test_truncated

    return ReviewPacket(
        task_goal=compact_goal,
        changed_files=tuple(changed_files),
        diff_stat=tuple(diff_stat),
        test_summary=compact_test_summary,
        focused_diff=focused_diff,
        warnings=tuple(warnings[:DEFAULT_MAX_WARNINGS]),
        risks=tuple(risks[:DEFAULT_MAX_RISKS]),
        truncated=truncated,
    )


def format_review_packet(packet: ReviewPacket) -> str:
    lines = [
        "Review Packet",
        "",
        f"Task goal: {packet.task_goal or '(none)'}",
        f"Changed files: {len(packet.changed_files)}",
        f"Test summary: {packet.test_summary or '(none)'}",
        "",
        "Files:",
    ]
    if packet.changed_files:
        lines.extend(f"- {path}" for path in packet.changed_files)
    else:
        lines.append("- (none)")
    lines.extend(("", "Diff stat:"))
    if packet.diff_stat:
        lines.extend(f"- {line}" for line in packet.diff_stat)
    else:
        lines.append("- (none)")
    if packet.focused_diff:
        lines.extend(("", "Focused diff:", packet.focused_diff))
    if packet.risks:
        lines.extend(("", "Risks:"))
        lines.extend(f"- {risk}" for risk in packet.risks)
    if packet.warnings:
        lines.extend(("", "Warnings:"))
        lines.extend(f"- {warning}" for warning in packet.warnings)
    if packet.truncated:
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


def _split_nonempty_lines(text: str) -> list[str]:
    return [line.rstrip() for line in text.splitlines() if line.strip()]


def _extract_changed_files(status_lines: list[str]) -> list[str]:
    changed_files: list[str] = []
    seen: set[str] = set()
    for line in status_lines:
        payload = line[3:] if len(line) > 3 else line
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1]
        path = payload.strip()
        if path and path not in seen:
            seen.add(path)
            changed_files.append(path)
    return changed_files


def _local_artifact_risks(status_lines: list[str]) -> list[str]:
    risks: list[str] = []
    for line in status_lines:
        payload = line[3:] if len(line) > 3 else line
        if " -> " in payload:
            payload = payload.split(" -> ", 1)[1]
        path = payload.strip()
        if not path:
            continue
        if _matches_prefix(path, IGNORED_LOCAL_PATHS):
            risks.append(f"local artifact path visible in git status: {path}")
        if "__pycache__" in path or path.endswith(".pyc"):
            risks.append(f"cache artifact visible in git status: {path}")
    return risks


def _sensitive_diff_risks(diff_text: str) -> list[str]:
    risks: list[str] = []
    if "BEGIN PRIVATE KEY" in diff_text:
        risks.append("focused diff may contain private key material")
    if "password" in diff_text.lower():
        risks.append("focused diff contains password-like text; review carefully")
    return risks


def _matches_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    normalized = path.rstrip("/")
    for prefix in prefixes:
        clean_prefix = prefix.rstrip("/")
        if normalized == clean_prefix or normalized.startswith(clean_prefix + "/"):
            return True
    return False


def _truncate_text(text: str, *, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[: max_chars - 1].rstrip() + "…", True
