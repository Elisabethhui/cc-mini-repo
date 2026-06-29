from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ScaffoldFile:
    rel_path: str
    content: str


WORKFLOW_SCAFFOLD: tuple[ScaffoldFile, ...] = (
    ScaffoldFile(
        rel_path="AGENTS.md",
        content=(
            "# Agent Development Guide\n\n"
            "This repository uses the context-bounded development workflow.\n"
        ),
    ),
    ScaffoldFile(
        rel_path=".ai-dev/README.md",
        content="# AI Dev\n\nThis repository uses the context-bounded workflow scaffold.\n",
    ),
    ScaffoldFile(
        rel_path=".ai-dev/WORKFLOW.md",
        content=(
            "# Workflow\n\n"
            "Use `/workflow-status` to inspect the scaffold and `/workflow-init` to add missing files.\n"
        ),
    ),
    ScaffoldFile(
        rel_path=".ai-dev/skills/.gitkeep",
        content="",
    ),
    ScaffoldFile(
        rel_path=".ai-dev/templates/CURRENT_TASK.md",
        content=(
            "# Current Task\n\n"
            "## Goal\n\n"
            "Describe the task outcome.\n\n"
            "## Boundaries\n\n"
            "- Product files\n"
            "- Tests\n"
            "- Verification\n"
        ),
    ),
    ScaffoldFile(
        rel_path=".ai-dev/templates/CONTEXT_PACK.md",
        content=(
            "# Context Pack\n\n"
            "## Scope\n\n"
            "Summarize the precise files and constraints required for the task.\n"
        ),
    ),
    ScaffoldFile(
        rel_path=".ai-dev/templates/TEST_GATE.md",
        content=(
            "# Test Gate\n\n"
            "## Commands\n\n"
            "- List the exact verification commands.\n"
        ),
    ),
    ScaffoldFile(
        rel_path=".ai-dev/templates/REVIEW_ROLLBACK.md",
        content=(
            "# Review And Rollback\n\n"
            "## Review\n\n"
            "- Note the highest-risk behavior changes.\n\n"
            "## Rollback\n\n"
            "- Record the exact revert command.\n"
        ),
    ),
    ScaffoldFile(
        rel_path=".ai-dev/templates/WORK_LOG.md",
        content=(
            "# Work Log\n\n"
            "## Summary\n\n"
            "- Record concise implementation notes and verification outcomes.\n"
        ),
    ),
)


@dataclass(frozen=True)
class WorkflowInitInspection:
    missing: tuple[str, ...]
    present: tuple[str, ...]
    conflicts: tuple[str, ...]


@dataclass(frozen=True)
class WorkflowInitResult:
    dry_run: bool
    created: tuple[str, ...]
    skipped: tuple[str, ...]
    conflicts: tuple[str, ...]


def inspect_workflow_scaffold(root: Path) -> WorkflowInitInspection:
    root = root.resolve()
    missing: list[str] = []
    present: list[str] = []
    conflicts: list[str] = []
    for scaffold in WORKFLOW_SCAFFOLD:
        status = _classify_target(root, scaffold.rel_path)
        if status == "missing":
            missing.append(scaffold.rel_path)
        elif status == "present":
            present.append(scaffold.rel_path)
        else:
            conflicts.append(scaffold.rel_path)
    return WorkflowInitInspection(
        missing=tuple(missing),
        present=tuple(present),
        conflicts=tuple(conflicts),
    )


def list_missing_workflow_files(root: Path) -> tuple[str, ...]:
    return inspect_workflow_scaffold(root).missing


def init_workflow_scaffold(root: Path, dry_run: bool = False) -> WorkflowInitResult:
    root = root.resolve()
    created: list[str] = []
    skipped: list[str] = []
    conflicts: list[str] = []
    for scaffold in WORKFLOW_SCAFFOLD:
        target = root / scaffold.rel_path
        status = _classify_target(root, scaffold.rel_path)
        if status == "present":
            skipped.append(scaffold.rel_path)
            continue
        if status == "conflict":
            conflicts.append(scaffold.rel_path)
            continue
        created.append(scaffold.rel_path)
        if dry_run:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            with target.open("x", encoding="utf-8") as handle:
                handle.write(scaffold.content)
        except FileExistsError:
            if target.is_file():
                created.pop()
                skipped.append(scaffold.rel_path)
            else:
                created.pop()
                conflicts.append(scaffold.rel_path)
    return WorkflowInitResult(
        dry_run=dry_run,
        created=tuple(created),
        skipped=tuple(skipped),
        conflicts=tuple(conflicts),
    )


def format_workflow_init_result(result: WorkflowInitResult) -> str:
    title = "Workflow init dry run" if result.dry_run else "Workflow init"
    sections = [
        title,
        "",
        _format_paths("Created", result.created),
        "",
        _format_paths("Skipped", result.skipped),
        "",
        _format_paths("Conflicts", result.conflicts),
    ]
    return "\n".join(sections).rstrip()


def _classify_target(root: Path, rel_path: str) -> str:
    target = root / rel_path
    if target.exists():
        return "present" if target.is_file() else "conflict"
    for parent in target.parents:
        if parent == root:
            break
        if parent.exists() and not parent.is_dir():
            return "conflict"
    return "missing"


def _format_paths(title: str, paths: tuple[str, ...]) -> str:
    lines = [f"{title}:"]
    if not paths:
        lines.append("- (none)")
        return "\n".join(lines)
    lines.extend(f"- {path}" for path in paths)
    return "\n".join(lines)
