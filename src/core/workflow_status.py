from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import shutil
import subprocess


REQUIRED_PATHS = (
    "AGENTS.md",
    ".ai-dev/README.md",
    ".ai-dev/WORKFLOW.md",
    ".ai-dev/skills/",
    ".ai-dev/templates/",
)

IGNORED_LOCAL_PATHS = (
    ".ai-dev/tasks/",
    ".ai-dev/context-packs/",
    ".ai-dev/worklogs/",
    ".ai-dev/checkpoints/",
    ".ai-dev/tmp/",
    ".codegraph/",
    ".codebase-memory/",
)


@dataclass(frozen=True)
class CheckResult:
    name: str
    ok: bool
    detail: str = ""


@dataclass(frozen=True)
class GitSummary:
    available: bool
    clean: bool
    entries: tuple[str, ...] = ()
    error: str = ""


@dataclass(frozen=True)
class WorkflowStatus:
    required_files: tuple[CheckResult, ...]
    ignored_paths: tuple[CheckResult, ...]
    codegraph: tuple[CheckResult, ...]
    git: tuple[CheckResult, ...]
    warnings: tuple[str, ...] = ()
    git_summary: GitSummary | None = None

    @property
    def ok(self) -> bool:
        checks = (
            self.required_files,
            self.ignored_paths,
            self.codegraph,
            self.git,
        )
        return all(item.ok for group in checks for item in group) and not self.warnings


def collect_workflow_status(root: Path) -> WorkflowStatus:
    root = root.resolve()
    git_summary = _get_git_summary(root)
    warnings = tuple(_build_warnings(git_summary))
    return WorkflowStatus(
        required_files=check_required_files(root),
        ignored_paths=check_ignored_paths(root),
        codegraph=check_codegraph(root),
        git=check_git_state(root, git_summary),
        warnings=warnings,
        git_summary=git_summary,
    )


def format_workflow_status(status: WorkflowStatus) -> str:
    lines = [
        f"Workflow status: {'OK' if status.ok else 'NEEDS ATTENTION'}",
        "",
        _format_section("Required Files", status.required_files),
        "",
        _format_section("Ignored Local Paths", status.ignored_paths),
        "",
        _format_section("CodeGraph", status.codegraph),
        "",
        _format_section("Git", status.git),
    ]
    if status.warnings:
        lines.extend(("", "Warnings:"))
        lines.extend(f"- {warning}" for warning in status.warnings)
    return "\n".join(lines).rstrip()


def check_required_files(root: Path) -> tuple[CheckResult, ...]:
    return tuple(_check_path(root, rel_path) for rel_path in REQUIRED_PATHS)


def check_ignored_paths(root: Path) -> tuple[CheckResult, ...]:
    return tuple(_check_path(root, rel_path) for rel_path in IGNORED_LOCAL_PATHS)


def check_codegraph(root: Path) -> tuple[CheckResult, ...]:
    command_available = shutil.which("codegraph") is not None
    codegraph_dir = root / ".codegraph"
    return (
        CheckResult(
            name="codegraph command",
            ok=command_available,
            detail="available" if command_available else "not installed",
        ),
        CheckResult(
            name=".codegraph/",
            ok=codegraph_dir.exists(),
            detail="present" if codegraph_dir.exists() else "not initialized",
        ),
    )


def check_git_state(root: Path, git_summary: GitSummary | None = None) -> tuple[CheckResult, ...]:
    summary = git_summary or _get_git_summary(root)
    if not summary.available:
        return (CheckResult(name="git status", ok=False, detail=summary.error or "git unavailable"),)
    return (
        CheckResult(
            name="git status",
            ok=summary.clean,
            detail="clean" if summary.clean else f"{len(summary.entries)} change(s)",
        ),
    )


def _check_path(root: Path, rel_path: str) -> CheckResult:
    path = root / rel_path.rstrip("/")
    exists = path.exists()
    kind = "directory" if rel_path.endswith("/") else "file"
    detail = f"{kind} present" if exists else f"{kind} missing"
    return CheckResult(name=rel_path, ok=exists, detail=detail)


def _get_git_summary(root: Path) -> GitSummary:
    if shutil.which("git") is None:
        return GitSummary(available=False, clean=False, error="git not installed")
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return GitSummary(available=False, clean=False, error=str(exc))
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"git exited {proc.returncode}"
        return GitSummary(available=False, clean=False, error=detail)
    entries = tuple(line for line in proc.stdout.splitlines() if line.strip())
    return GitSummary(available=True, clean=not entries, entries=entries)


def _build_warnings(git_summary: GitSummary | None) -> list[str]:
    if git_summary is None or not git_summary.available:
        return []
    warnings: list[str] = []
    for entry in git_summary.entries:
        path = _extract_status_path(entry)
        if not path:
            continue
        if _matches_prefix(path, IGNORED_LOCAL_PATHS):
            warnings.append(f"local workflow artifact visible in git status: {path}")
        if "__pycache__" in path or path.endswith(".pyc"):
            warnings.append(f"cache artifact visible in git status: {path}")
    return warnings


def _extract_status_path(entry: str) -> str:
    payload = entry[3:] if len(entry) > 3 else entry
    if " -> " in payload:
        return payload.split(" -> ", 1)[1].strip()
    return payload.strip()


def _matches_prefix(path: str, prefixes: tuple[str, ...]) -> bool:
    normalized = path.rstrip("/")
    for prefix in prefixes:
        clean_prefix = prefix.rstrip("/")
        if normalized == clean_prefix or normalized.startswith(clean_prefix + "/"):
            return True
    return False


def _format_section(title: str, checks: tuple[CheckResult, ...]) -> str:
    lines = [f"{title}:"]
    for check in checks:
        marker = "OK" if check.ok else "MISSING"
        detail = f" ({check.detail})" if check.detail else ""
        lines.append(f"- [{marker}] {check.name}{detail}")
    return "\n".join(lines)
