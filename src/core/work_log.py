from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


DEFAULT_MAX_FILES = 12
DEFAULT_MAX_ITEMS = 6
DEFAULT_MAX_TEXT_CHARS = 240
WORKLOG_DIR = ".ai-dev/worklogs"


@dataclass(frozen=True)
class WorkLogEntry:
    task_id: str
    goal: str
    changed_files: tuple[str, ...]
    tests: tuple[str, ...]
    review_result: str
    risks: tuple[str, ...]
    next_step: str
    truncated: bool = False


def render_work_log(entry: WorkLogEntry) -> str:
    lines = [
        f"# Work Log: {entry.task_id}",
        "",
        "## Goal",
        _dash_or_text(entry.goal),
        "",
        "## Changed Files",
    ]
    lines.extend(_render_list(entry.changed_files))
    lines.extend(("", "## Verification"))
    lines.extend(_render_list(entry.tests))
    lines.extend(("", "## Review Decision", _dash_or_text(entry.review_result)))
    lines.extend(("", "## Remaining Risk"))
    lines.extend(_render_list(entry.risks))
    lines.extend(("", "## Next Task", _dash_or_text(entry.next_step)))
    if entry.truncated:
        lines.extend(("", "## Note", "- truncated for safety"))
    return "\n".join(lines).rstrip()


def build_work_log_entry(
    *,
    task_id: str,
    goal: str,
    changed_files: list[str] | tuple[str, ...],
    tests: list[str] | tuple[str, ...],
    review_result: str,
    risks: list[str] | tuple[str, ...],
    next_step: str,
) -> WorkLogEntry:
    truncated = False
    safe_goal, goal_truncated = _compact_text(goal)
    safe_review, review_truncated = _compact_text(review_result)
    safe_next_step, next_truncated = _compact_text(next_step)
    safe_files, files_truncated = _compact_items(changed_files, max_items=DEFAULT_MAX_FILES)
    safe_tests, tests_truncated = _compact_items(tests, max_items=DEFAULT_MAX_ITEMS)
    safe_risks, risks_truncated = _compact_items(risks, max_items=DEFAULT_MAX_ITEMS)
    truncated = any(
        (
            goal_truncated,
            review_truncated,
            next_truncated,
            files_truncated,
            tests_truncated,
            risks_truncated,
        )
    )
    return WorkLogEntry(
        task_id=_safe_task_id(task_id),
        goal=safe_goal,
        changed_files=safe_files,
        tests=safe_tests,
        review_result=safe_review,
        risks=safe_risks,
        next_step=safe_next_step,
        truncated=truncated,
    )


def write_work_log(root: Path, entry: WorkLogEntry) -> Path:
    root = root.resolve()
    worklog_dir = (root / WORKLOG_DIR).resolve()
    worklog_dir.mkdir(parents=True, exist_ok=True)
    path = (worklog_dir / f"{entry.task_id}.md").resolve()
    if not _is_within_directory(path, worklog_dir):
        raise ValueError("work log path must stay within .ai-dev/worklogs/")
    path.write_text(render_work_log(entry) + "\n", encoding="utf-8")
    return path


def _safe_task_id(task_id: str) -> str:
    normalized = task_id.strip() or "task-unknown"
    normalized = normalized.replace("\\", "/").split("/")[-1]
    normalized = re.sub(r"[^A-Za-z0-9._-]+", "-", normalized)
    return normalized or "task-unknown"


def _compact_items(items: list[str] | tuple[str, ...], *, max_items: int) -> tuple[tuple[str, ...], bool]:
    compacted: list[str] = []
    truncated = False
    for item in items:
        safe_item, item_truncated = _compact_text(item)
        if safe_item:
            compacted.append(safe_item)
        truncated = truncated or item_truncated
    if len(compacted) > max_items:
        compacted = compacted[:max_items]
        truncated = True
    return tuple(compacted), truncated


def _compact_text(text: str) -> tuple[str, bool]:
    compact = _redact_sensitive_text(" ".join(text.strip().split()))
    if len(compact) <= DEFAULT_MAX_TEXT_CHARS:
        return compact, False
    return compact[: DEFAULT_MAX_TEXT_CHARS - 1].rstrip() + "…", True


def _redact_sensitive_text(text: str) -> str:
    redacted = re.sub(r"(?i)(password\s*[:=]\s*)(\S+)", r"\1[redacted]", text)
    redacted = re.sub(r"(?i)(secret\s*[:=]\s*)(\S+)", r"\1[redacted]", redacted)
    redacted = re.sub(r"(?i)(token\s*[:=]\s*)(\S+)", r"\1[redacted]", redacted)
    return redacted


def _render_list(items: tuple[str, ...]) -> list[str]:
    if not items:
        return ["-"]
    return [f"- {item}" for item in items]


def _dash_or_text(text: str) -> str:
    return text or "-"


def _is_within_directory(path: Path, directory: Path) -> bool:
    try:
        path.relative_to(directory)
        return True
    except ValueError:
        return False
