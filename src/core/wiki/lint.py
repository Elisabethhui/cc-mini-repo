"""
Lint / Health Check module (Phase 5)
Performs health checks on .cc-mini/wiki/ structure.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from enum import Enum


class CheckStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"
    MISSING = "missing"


@dataclass
class CheckResult:
    """Single check result"""
    check_name: str = ""
    status: CheckStatus = CheckStatus.OK
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "check_name": self.check_name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
        }


class WikiLinter:
    """
    Phase 5: Health check for .cc-mini/wiki/ structure.
    """

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root).resolve()
        self.cc_mini_dir = self.workspace / ".cc-mini"
        self.wiki_dir = self.cc_mini_dir / "wiki"
        self.results: list[CheckResult] = []

    def run_all_checks(self) -> dict[str, Any]:
        """Run all health checks and return report."""
        self.results = []

        # Core structure checks
        self._check_wiki_dir_exists()
        self._check_index_md()
        self._check_entities_dir()
        self._check_taskpacks_dir()
        self._check_reports_dir()

        # Orphan checks
        self._check_orphan_taskpacks()
        self._check_orphan_snapshots()
        self._check_orphan_reports()

        # Consistency checks
        self._check_entity_consistency()

        # Generate report
        report = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "workspace": str(self.workspace),
            "summary": self._summarize(),
            "checks": [r.to_dict() for r in self.results],
        }

        return report

    def _check_wiki_dir_exists(self) -> None:
        """Check if .cc-mini/wiki/ exists."""
        if self.wiki_dir.exists():
            self.results.append(CheckResult(
                check_name="wiki_dir_exists",
                status=CheckStatus.OK,
                message=".cc-mini/wiki/ directory exists",
            ))
        else:
            self.results.append(CheckResult(
                check_name="wiki_dir_exists",
                status=CheckStatus.MISSING,
                message=".cc-mini/wiki/ directory does not exist",
            ))

    def _check_index_md(self) -> None:
        """Check if index.md exists."""
        index_file = self.wiki_dir / "index.md"
        if index_file.exists():
            self.results.append(CheckResult(
                check_name="index_md_exists",
                status=CheckStatus.OK,
                message="index.md exists",
                details={"size_bytes": index_file.stat().st_size},
            ))
        else:
            self.results.append(CheckResult(
                check_name="index_md_exists",
                status=CheckStatus.MISSING,
                message="index.md is missing",
            ))

    def _check_entities_dir(self) -> None:
        """Check entities directory."""
        entities_dir = self.wiki_dir / "entities"
        if not entities_dir.exists():
            self.results.append(CheckResult(
                check_name="entities_dir",
                status=CheckStatus.MISSING,
                message="entities/ directory is missing",
            ))
            return

        entity_files = list(entities_dir.glob("*.md"))
        stale_count = 0
        error_count = 0

        for ef in entity_files:
            try:
                content = ef.read_text(encoding="utf-8")
                if "status: stale" in content:
                    stale_count += 1
                elif "status: error" in content:
                    error_count += 1
            except Exception:
                pass

        status = CheckStatus.OK
        message = f"{len(entity_files)} entities found"
        if stale_count > 0 or error_count > 0:
            status = CheckStatus.WARNING
            message += f" ({stale_count} stale, {error_count} error)"

        self.results.append(CheckResult(
            check_name="entities_dir",
            status=status,
            message=message,
            details={
                "total": len(entity_files),
                "stale": stale_count,
                "error": error_count,
            },
        ))

    def _check_taskpacks_dir(self) -> None:
        """Check taskpacks directory."""
        taskpacks_dir = self.wiki_dir / "taskpacks"
        if taskpacks_dir.exists():
            count = len(list(taskpacks_dir.glob("*.json")))
            self.results.append(CheckResult(
                check_name="taskpacks_dir",
                status=CheckStatus.OK,
                message=f"{count} taskpacks found",
                details={"count": count},
            ))
        else:
            self.results.append(CheckResult(
                check_name="taskpacks_dir",
                status=CheckStatus.MISSING,
                message="taskpacks/ directory is missing",
            ))

    def _check_reports_dir(self) -> None:
        """Check reports directory structure."""
        reports_dir = self.wiki_dir / "reports"
        if not reports_dir.exists():
            self.results.append(CheckResult(
                check_name="reports_dir",
                status=CheckStatus.MISSING,
                message="reports/ directory is missing",
            ))
            return

        # Check subdirectories
        subdirs = ["deferred-issues", "micro-forks"]
        missing = []
        for subdir in subdirs:
            if not (reports_dir / subdir).exists():
                missing.append(subdir)

        if missing:
            self.results.append(CheckResult(
                check_name="reports_dir",
                status=CheckStatus.WARNING,
                message=f"Missing subdirectories: {', '.join(missing)}",
            ))
        else:
            self.results.append(CheckResult(
                check_name="reports_dir",
                status=CheckStatus.OK,
                message="reports/ structure is complete",
            ))

    def _check_orphan_taskpacks(self) -> None:
        """Check for orphaned taskpacks (no corresponding source files)."""
        taskpacks_dir = self.wiki_dir / "taskpacks"
        if not taskpacks_dir.exists():
            return

        orphans = []
        for tp in taskpacks_dir.glob("*.json"):
            try:
                data = json.loads(tp.read_text())
                target_files = data.get("target_files", [])

                # Check if target files exist
                missing = []
                for tf in target_files:
                    if not (self.workspace / tf).exists():
                        missing.append(tf)

                if missing:
                    orphans.append({"taskpack": tp.name, "missing_files": missing})
            except Exception:
                pass

        if orphans:
            self.results.append(CheckResult(
                check_name="orphan_taskpacks",
                status=CheckStatus.WARNING,
                message=f"{len(orphans)} taskpacks with missing source files",
                details={"orphans": orphans},
            ))
        else:
            self.results.append(CheckResult(
                check_name="orphan_taskpacks",
                status=CheckStatus.OK,
                message="No orphaned taskpacks found",
            ))

    def _check_orphan_snapshots(self) -> None:
        """Check for old snapshots that should be archived."""
        snapshots_dir = self.wiki_dir / "snapshots"
        if not snapshots_dir.exists():
            return

        old_snapshots = []
        for snapshot in snapshots_dir.glob("*.json"):
            mtime = datetime.fromtimestamp(snapshot.stat().st_mtime, timezone.utc)
            age_days = (datetime.now(timezone.utc) - mtime).days
            if age_days > 7:
                old_snapshots.append({"file": snapshot.name, "age_days": age_days})

        if old_snapshots:
            self.results.append(CheckResult(
                check_name="orphan_snapshots",
                status=CheckStatus.WARNING,
                message=f"{len(old_snapshots)} old snapshots (>7 days)",
                details={"old_snapshots": old_snapshots},
            ))
        else:
            self.results.append(CheckResult(
                check_name="orphan_snapshots",
                status=CheckStatus.OK,
                message="No old snapshots found",
            ))

    def _check_orphan_reports(self) -> None:
        """Check for orphaned reports."""
        reports_dir = self.wiki_dir / "reports"
        if not reports_dir.exists():
            return

        # Count deferred issues and micro-forks
        deferred_count = len(list((reports_dir / "deferred-issues").glob("*.json"))) if (reports_dir / "deferred-issues").exists() else 0
        forks_count = len(list((reports_dir / "micro-forks").glob("*.json"))) if (reports_dir / "micro-forks").exists() else 0

        self.results.append(CheckResult(
            check_name="orphan_reports",
            status=CheckStatus.OK,
            message=f"Reports: {deferred_count} deferred issues, {forks_count} micro-forks",
            details={
                "deferred_issues": deferred_count,
                "micro_forks": forks_count,
            },
        ))

    def _check_entity_consistency(self) -> None:
        """Check entity files for consistency."""
        entities_dir = self.wiki_dir / "entities"
        if not entities_dir.exists():
            return

        issues = []
        for ef in entities_dir.glob("*.md"):
            try:
                content = ef.read_text(encoding="utf-8")
                # Check for required frontmatter
                if "---" not in content:
                    issues.append({"file": ef.name, "issue": "missing frontmatter"})
                elif "status:" not in content:
                    issues.append({"file": ef.name, "issue": "missing status field"})
            except Exception as e:
                issues.append({"file": ef.name, "issue": f"read error: {e}"})

        if issues:
            self.results.append(CheckResult(
                check_name="entity_consistency",
                status=CheckStatus.WARNING,
                message=f"{len(issues)} entities with consistency issues",
                details={"issues": issues[:10]},  # Limit details
            ))
        else:
            self.results.append(CheckResult(
                check_name="entity_consistency",
                status=CheckStatus.OK,
                message="All entities are consistent",
            ))

    def _summarize(self) -> dict[str, int]:
        """Summarize check results."""
        counts = {"ok": 0, "warning": 0, "error": 0, "missing": 0}
        for r in self.results:
            counts[r.status.value] += 1
        return counts
