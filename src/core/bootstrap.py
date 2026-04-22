from __future__ import annotations

from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path

__all__ = [
    "BootstrapResult",
    "BootstrapStatus",
    "bootstrap_workspace",
    "doctor_workspace",
    "ensure_phase1_workspace",
    "inspect_phase1_workspace",
]


class BootstrapStatus(str, Enum):
    MISSING = "missing"
    STALE = "stale"
    INITIALIZED = "initialized"


@dataclass(frozen=True)
class BootstrapResult:
    workspace: Path
    cc_mini_dir: Path
    wiki_dir: Path
    index_file: Path
    entities_dir: Path
    taskpacks_dir: Path
    reports_dir: Path
    status: BootstrapStatus
    created_paths: tuple[Path, ...] = ()
    missing_paths: tuple[Path, ...] = ()
    stale_paths: tuple[Path, ...] = ()
    notes: tuple[str, ...] = ()

    @property
    def ready(self) -> bool:
        return self.status == BootstrapStatus.INITIALIZED

    @property
    def is_ready(self) -> bool:
        return self.ready


_INDEX_TEMPLATE = """# cc-mini Phase 1 Workspace

This directory was bootstrapped for the minimal Phase 1 product path.

## Scaffold

- `.cc-mini/`
- `.cc-mini/wiki/`
- `.cc-mini/wiki/index.md`
- `.cc-mini/wiki/entities/`
- `.cc-mini/wiki/taskpacks/`
- `.cc-mini/wiki/reports/`
"""


def bootstrap_workspace(workspace_root: str | Path) -> BootstrapResult:
    workspace = Path(workspace_root).resolve()
    current = inspect_phase1_workspace(workspace)

    created: list[Path] = []
    for path in (current.cc_mini_dir, current.wiki_dir, current.entities_dir, current.taskpacks_dir, current.reports_dir):
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            created.append(path)

    if not current.index_file.exists() or current.index_file.stat().st_size == 0:
        current.index_file.write_text(_INDEX_TEMPLATE, encoding="utf-8")
        created.append(current.index_file)

    return replace(inspect_phase1_workspace(workspace), created_paths=tuple(created))


def ensure_phase1_workspace(workspace_root: str | Path) -> BootstrapResult:
    return bootstrap_workspace(workspace_root)


def inspect_phase1_workspace(workspace_root: str | Path) -> BootstrapResult:
    workspace = Path(workspace_root).resolve()
    cc_mini_dir = workspace / ".cc-mini"
    wiki_dir = cc_mini_dir / "wiki"
    index_file = wiki_dir / "index.md"
    entities_dir = wiki_dir / "entities"
    taskpacks_dir = wiki_dir / "taskpacks"
    reports_dir = wiki_dir / "reports"

    required_paths = (cc_mini_dir, wiki_dir, index_file, entities_dir, taskpacks_dir, reports_dir)
    missing_paths = tuple(path for path in required_paths if not path.exists())

    if not cc_mini_dir.exists():
        status = BootstrapStatus.MISSING
        stale_paths: tuple[Path, ...] = ()
    elif not wiki_dir.exists():
        status = BootstrapStatus.STALE
        stale_paths = missing_paths
    elif missing_paths:
        status = BootstrapStatus.STALE
        stale_paths = missing_paths
    else:
        status = BootstrapStatus.INITIALIZED
        stale_paths = ()

    notes = _build_notes(status, missing_paths)
    return BootstrapResult(
        workspace=workspace,
        cc_mini_dir=cc_mini_dir,
        wiki_dir=wiki_dir,
        index_file=index_file,
        entities_dir=entities_dir,
        taskpacks_dir=taskpacks_dir,
        reports_dir=reports_dir,
        status=status,
        missing_paths=missing_paths,
        stale_paths=stale_paths,
        notes=notes,
    )


def doctor_workspace(workspace_root: str | Path) -> BootstrapResult:
    return inspect_phase1_workspace(workspace_root)


def _build_notes(status: BootstrapStatus, missing_paths: tuple[Path, ...]) -> tuple[str, ...]:
    if status == BootstrapStatus.INITIALIZED:
        return ("phase1 workspace is ready",)
    if status == BootstrapStatus.MISSING:
        return ("phase1 workspace scaffold is not present",)
    return tuple(f"missing: {path}" for path in missing_paths)
