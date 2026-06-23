from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess

from .workflow_status import IGNORED_LOCAL_PATHS, REQUIRED_PATHS


SEVERITY_ORDER = {
    "ok": 0,
    "warn": 1,
    "fail": 2,
    "blocked": 3,
}


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    severity: str
    detail: str


@dataclass(frozen=True)
class WorkflowDoctorReport:
    required_files: tuple[DoctorCheck, ...]
    local_artifacts: tuple[DoctorCheck, ...]
    markdown: tuple[DoctorCheck, ...]
    codegraph: tuple[DoctorCheck, ...]
    decision: str

    @property
    def ok(self) -> bool:
        return self.decision == "ok"


def collect_workflow_doctor_report(root: Path) -> WorkflowDoctorReport:
    root = root.resolve()
    required_files = check_required_workflow_files(root)
    local_artifacts = check_local_artifacts(root)
    markdown = check_markdown_code_fences(root)
    codegraph = check_codegraph_availability(root)
    decision = _derive_decision(required_files, local_artifacts, markdown, codegraph)
    return WorkflowDoctorReport(
        required_files=required_files,
        local_artifacts=local_artifacts,
        markdown=markdown,
        codegraph=codegraph,
        decision=decision,
    )


def format_workflow_doctor_report(report: WorkflowDoctorReport) -> str:
    lines = [
        "Context-Bounded Workflow Doctor",
        "",
        _format_section("Required Files", report.required_files),
        "",
        _format_section("Local Artifacts", report.local_artifacts),
        "",
        _format_section("Markdown", report.markdown),
        "",
        _format_section("CodeGraph", report.codegraph),
        "",
        f"Decision: {report.decision}",
    ]
    return "\n".join(lines).rstrip()


def check_required_workflow_files(root: Path) -> tuple[DoctorCheck, ...]:
    checks: list[DoctorCheck] = []
    for rel_path in REQUIRED_PATHS:
        target = root / rel_path.rstrip("/")
        kind = "directory" if rel_path.endswith("/") else "file"
        if target.exists():
            checks.append(DoctorCheck(rel_path, "ok", f"{kind} present"))
        else:
            checks.append(DoctorCheck(rel_path, "fail", f"{kind} missing"))
    return tuple(checks)


def check_local_artifacts(root: Path) -> tuple[DoctorCheck, ...]:
    summary = _get_git_summary(root)
    if not summary.available:
        return (DoctorCheck("git status", "warn", summary.error or "git unavailable"),)

    checks: list[DoctorCheck] = []
    entries = summary.entries
    for entry in entries:
        path = _extract_status_path(entry)
        if not path:
            continue
        if _matches_prefix(path, IGNORED_LOCAL_PATHS):
            checks.append(_artifact_check_for_entry(entry, path, label="local workflow artifact"))
            continue
        if "__pycache__" in path or path.endswith(".pyc"):
            checks.append(_artifact_check_for_entry(entry, path, label="cache artifact"))
    if not checks:
        return (DoctorCheck("git artifacts", "ok", "no tracked or staged local artifacts"),)
    return tuple(checks)


def check_markdown_code_fences(root: Path) -> tuple[DoctorCheck, ...]:
    checks: list[DoctorCheck] = []
    for rel_path in _markdown_targets(root):
        target = root / rel_path
        if not target.exists() or not target.is_file():
            continue
        if _has_closed_code_fences(target):
            checks.append(DoctorCheck(rel_path, "ok", "code fences closed"))
        else:
            checks.append(DoctorCheck(rel_path, "fail", "unclosed code fence"))
    if not checks:
        return (DoctorCheck("markdown files", "ok", "no workflow markdown files to check"),)
    return tuple(checks)


def check_codegraph_availability(root: Path) -> tuple[DoctorCheck, ...]:
    command_available = shutil.which("codegraph") is not None
    checks = [
        DoctorCheck(
            "codegraph command",
            "ok" if command_available else "warn",
            "available" if command_available else "not installed",
        )
    ]
    codegraph_dir = root / ".codegraph"
    checks.append(
        DoctorCheck(
            ".codegraph/",
            "ok" if codegraph_dir.exists() else "warn",
            "present" if codegraph_dir.exists() else "not initialized",
        )
    )
    return tuple(checks)


@dataclass(frozen=True)
class GitSummary:
    available: bool
    entries: tuple[str, ...] = ()
    error: str = ""


def _artifact_check_for_entry(entry: str, path: str, label: str) -> DoctorCheck:
    staged = _is_staged_entry(entry)
    tracked = _is_tracked_entry(entry)
    if staged:
        return DoctorCheck(path, "blocked", f"{label} staged in git")
    if tracked:
        return DoctorCheck(path, "fail", f"{label} tracked by git")
    return DoctorCheck(path, "warn", f"{label} visible in git status")


def _derive_decision(*groups: tuple[DoctorCheck, ...]) -> str:
    max_severity = "ok"
    for group in groups:
        for check in group:
            if SEVERITY_ORDER[check.severity] > SEVERITY_ORDER[max_severity]:
                max_severity = check.severity
    return max_severity


def _format_section(title: str, checks: tuple[DoctorCheck, ...]) -> str:
    lines = [f"{title}:"]
    for check in checks:
        lines.append(f"- [{check.severity.upper()}] {check.name} ({check.detail})")
    return "\n".join(lines)


def _get_git_summary(root: Path) -> GitSummary:
    if shutil.which("git") is None:
        return GitSummary(available=False, error="git not installed")
    try:
        proc = subprocess.run(
            ["git", "status", "--short"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        return GitSummary(available=False, error=str(exc))
    if proc.returncode != 0:
        detail = proc.stderr.strip() or proc.stdout.strip() or f"git exited {proc.returncode}"
        return GitSummary(available=False, error=detail)
    entries = tuple(line for line in proc.stdout.splitlines() if line.strip())
    return GitSummary(available=True, entries=entries)


def _markdown_targets(root: Path) -> tuple[str, ...]:
    targets: list[str] = ["AGENTS.md", ".ai-dev/README.md", ".ai-dev/WORKFLOW.md"]
    for folder in (".ai-dev/templates", ".ai-dev/skills"):
        base = root / folder
        if not base.exists() or not base.is_dir():
            continue
        for path in sorted(base.rglob("*.md")):
            if path.is_file():
                targets.append(path.relative_to(root).as_posix())
    return tuple(targets)


def _has_closed_code_fences(path: Path) -> bool:
    in_fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
    return not in_fence


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


def _is_staged_entry(entry: str) -> bool:
    return len(entry) >= 1 and entry[0] not in {" ", "?"}


def _is_tracked_entry(entry: str) -> bool:
    if len(entry) < 2:
        return False
    return entry[1] not in {" ", "?"}
