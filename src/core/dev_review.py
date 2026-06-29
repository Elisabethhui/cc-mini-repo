from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .dev_contract import DevReviewResult, TaskResult


WORKLOG_DIR = ".ai-dev/worklogs"
_MAX_LINE_CHARS = 240
_MAX_LIST_ITEMS = 12


def review_task_result(task_result: TaskResult) -> DevReviewResult:
    """Produce a safe review decision for a finished task.

    Rules:
    - passed with no scope/forbidden risks -> pass / can_finish / requires_user_commit
    - failed (including after retry) -> revise / cannot finish
    - blocked because of forbidden/scope violation -> blocked / cannot finish
    - split / needs_planning -> blocked / cannot finish
    - review_decision is never "commit".
    """
    risks = list(task_result.risks)
    status = task_result.status

    has_scope_risk = any(
        phrase in r.lower()
        for r in risks
        for phrase in ("forbidden", "out-of-bounds", "scope")
    )

    if status == "passed" and task_result.verification_passed and not has_scope_risk:
        return DevReviewResult(
            task_id=task_result.task_id,
            review_decision="pass",
            can_finish=True,
            requires_user_commit=True,
            risks=risks,
            next_action=f"Task {task_result.task_id} passed; review changes and commit manually",
        )

    if status == "failed":
        return DevReviewResult(
            task_id=task_result.task_id,
            review_decision="revise",
            can_finish=False,
            requires_user_commit=False,
            risks=risks,
            next_action=f"Fix failures for {task_result.task_id} and rerun",
        )

    # blocked / split / needs_planning / unknown terminal state
    return DevReviewResult(
        task_id=task_result.task_id,
        review_decision="blocked",
        can_finish=False,
        requires_user_commit=False,
        risks=risks,
        next_action=task_result.next_action or f"Resolve blockers for {task_result.task_id}",
    )


def _safe_run_id(run_id: str) -> str:
    run_id = (run_id or "unknown").strip()
    run_id = run_id.replace("\\", "/").split("/")[-1]
    run_id = re.sub(r"[^A-Za-z0-9._-]+", "-", run_id)
    return run_id or "unknown"


def _compact_line(text: str) -> str:
    compact = " ".join(str(text).strip().split())
    if len(compact) <= _MAX_LINE_CHARS:
        return compact
    return compact[: _MAX_LINE_CHARS - 1].rstrip() + "…"


def _compact_list(items: list[str]) -> list[str]:
    compacted: list[str] = []
    for item in items:
        line = _compact_line(item)
        if line:
            compacted.append(line)
    if len(compacted) > _MAX_LIST_ITEMS:
        compacted = compacted[:_MAX_LIST_ITEMS]
        compacted.append("…")
    return compacted


def render_dev_worklog(
    *,
    run_id: str,
    task_result: TaskResult,
    review_result: DevReviewResult,
) -> str:
    """Render a dev worklog markdown document."""
    task_id = task_result.task_id
    spec_path = f".ai-dev/runtime/{run_id}/tasks/{task_id}.json"
    status = task_result.status
    changed = _compact_list(list(task_result.changed_files))
    verification_cmd = _compact_list(list(task_result.verification_command))
    risks = _compact_list(list(task_result.risks))

    lines = [
        f"# Dev Worklog: {task_id}",
        "",
        f"- **run_id:** {run_id}",
        f"- **task_id:** {task_id}",
        f"- **task_spec_path:** {spec_path}",
        f"- **goal:** {_compact_line(task_result.notes or '')}",
        "",
        "## Changed Files",
    ]
    lines.extend(f"- {f}" for f in changed) or lines.append("-")
    lines.extend(("", "## Verification Command"))
    lines.extend(f"- {c}" for c in verification_cmd) or lines.append("-")
    lines.extend(("", "## Attempts"))
    lines.append(f"- attempts: {task_result.attempts}")
    lines.append(f"- retry_count: {task_result.retry_count}")
    lines.append(f"- final_test_passed: {task_result.final_test_passed}")
    lines.extend(("", "## Final Status"))
    lines.append(f"- status: {status}")
    lines.append(f"- verification_passed: {task_result.verification_passed}")
    lines.extend(("", "## Review Decision"))
    lines.append(f"- decision: {review_result.review_decision}")
    lines.append(f"- can_finish: {review_result.can_finish}")
    lines.append(f"- requires_user_commit: {review_result.requires_user_commit}")
    lines.extend(("", "## Risks"))
    lines.extend(f"- {r}" for r in risks) or lines.append("-")
    lines.extend(("", "## Next Action"))
    lines.append(f"- {_compact_line(review_result.next_action)}")
    return "\n".join(lines) + "\n"


def write_dev_worklog(
    workspace: Path,
    run_id: str,
    task_result: TaskResult,
    review_result: DevReviewResult,
) -> Path:
    """Write the dev worklog to ``.ai-dev/worklogs/<run-id>.md``.

    Returns the absolute path of the written file.
    """
    root = Path(workspace).expanduser().resolve()
    worklog_dir = (root / WORKLOG_DIR).resolve()
    worklog_dir.mkdir(parents=True, exist_ok=True)

    safe_run_id = _safe_run_id(run_id)
    path = (worklog_dir / f"{safe_run_id}.md").resolve()
    # Defensive: ensure the resolved path is still inside worklog_dir.
    try:
        path.relative_to(worklog_dir)
    except ValueError as exc:
        raise ValueError(f"worklog path escapes worklog directory: {path}") from exc

    content = render_dev_worklog(
        run_id=safe_run_id,
        task_result=task_result,
        review_result=review_result,
    )
    path.write_text(content, encoding="utf-8")
    return path


def apply_review_to_task_result(
    task_result: TaskResult,
    review_result: DevReviewResult,
    worklog_path: Path | None = None,
) -> TaskResult:
    """Mutate a TaskResult with review fields and return it."""
    task_result.review_decision = review_result.review_decision
    task_result.can_finish = review_result.can_finish
    task_result.requires_user_commit = review_result.requires_user_commit
    if worklog_path is not None:
        task_result.worklog_path = str(worklog_path)
    return task_result
