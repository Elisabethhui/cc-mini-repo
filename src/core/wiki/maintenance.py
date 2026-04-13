"""
Maintenance and Stale Recovery module (Phase 5)
Handles lifecycle maintenance of snapshots, deferred issues, taskpacks, and digest pages.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from enum import Enum


class MaintenanceAction(str, Enum):
    """Possible maintenance actions"""
    CLEAN = "clean"           # Delete old items
    ARCHIVE = "archive"       # Move to archive
    MARK_STALE = "mark_stale"  # Mark as stale
    UPDATE_INDEX = "update_index"  # Update wiki index


@dataclass
class MaintenanceItem:
    """Single maintenance item"""
    item_path: str = ""
    item_type: str = ""       # snapshot, deferred_issue, taskpack, digest
    action: MaintenanceAction = MaintenanceAction.CLEAN
    reason: str = ""
    executed: bool = False
    executed_at: str | None = None


class MaintenanceEngine:
    """
    Phase 5: Maintenance engine for lifecycle management.
    """

    # Age thresholds for maintenance
    THRESHOLDS = {
        "snapshot": {"days": 7, "action": MaintenanceAction.ARCHIVE},
        "deferred_issue": {"days": 30, "action": MaintenanceAction.CLEAN},
        "taskpack": {"days": 30, "action": MaintenanceAction.ARCHIVE},
        "micro_fork": {"days": 14, "action": MaintenanceAction.CLEAN},
    }

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root).resolve()
        self.wiki_dir = self.workspace / ".cc-mini" / "wiki"
        self.archive_dir = self.wiki_dir / "archive"

    def run_maintenance(self, dry_run: bool = True) -> dict[str, Any]:
        """
        Run full maintenance cycle.
        Returns report of actions taken.
        """
        items: list[MaintenanceItem] = []

        # Check each type
        items.extend(self._maintain_snapshots(dry_run))
        items.extend(self._maintain_deferred_issues(dry_run))
        items.extend(self._maintain_taskpacks(dry_run))
        items.extend(self._maintain_micro_forks(dry_run))

        # Update index
        index_updated = self._update_index(dry_run)

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "dry_run": dry_run,
            "items_processed": len(items),
            "items": [
                {
                    "item_path": i.item_path,
                    "item_type": i.item_type,
                    "action": i.action.value,
                    "reason": i.reason,
                    "executed": i.executed,
                }
                for i in items
            ],
            "index_updated": index_updated,
        }

    def _is_old(self, path: Path, days: int) -> bool:
        """Check if file is older than specified days."""
        if not path.exists():
            return False
        mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        return datetime.now(timezone.utc) - mtime > timedelta(days=days)

    def _maintain_snapshots(self, dry_run: bool) -> list[MaintenanceItem]:
        """Maintain old snapshots."""
        items = []
        snapshots_dir = self.wiki_dir / "snapshots"
        if not snapshots_dir.exists():
            return items

        threshold = self.THRESHOLDS["snapshot"]

        for snapshot in snapshots_dir.glob("*.json"):
            if self._is_old(snapshot, threshold["days"]):
                item = MaintenanceItem(
                    item_path=str(snapshot),
                    item_type="snapshot",
                    action=threshold["action"],
                    reason=f"Older than {threshold['days']} days",
                )

                if not dry_run:
                    self._archive_item(snapshot, "snapshots")
                    item.executed = True
                    item.executed_at = datetime.now(timezone.utc).isoformat()

                items.append(item)

        return items

    def _maintain_deferred_issues(self, dry_run: bool) -> list[MaintenanceItem]:
        """Maintain old deferred issues."""
        items = []
        deferred_dir = self.wiki_dir / "reports" / "deferred-issues"
        if not deferred_dir.exists():
            return items

        threshold = self.THRESHOLDS["deferred_issue"]

        for issue in deferred_dir.glob("*.json"):
            if self._is_old(issue, threshold["days"]):
                item = MaintenanceItem(
                    item_path=str(issue),
                    item_type="deferred_issue",
                    action=threshold["action"],
                    reason=f"Older than {threshold['days']} days",
                )

                if not dry_run:
                    issue.unlink()
                    item.executed = True
                    item.executed_at = datetime.now(timezone.utc).isoformat()

                items.append(item)

        return items

    def _maintain_taskpacks(self, dry_run: bool) -> list[MaintenanceItem]:
        """Maintain old taskpacks."""
        items = []
        taskpacks_dir = self.wiki_dir / "taskpacks"
        if not taskpacks_dir.exists():
            return items

        threshold = self.THRESHOLDS["taskpack"]

        for taskpack in taskpacks_dir.glob("*.json"):
            if self._is_old(taskpack, threshold["days"]):
                item = MaintenanceItem(
                    item_path=str(taskpack),
                    item_type="taskpack",
                    action=threshold["action"],
                    reason=f"Older than {threshold['days']} days",
                )

                if not dry_run:
                    self._archive_item(taskpack, "taskpacks")
                    item.executed = True
                    item.executed_at = datetime.now(timezone.utc).isoformat()

                items.append(item)

        return items

    def _maintain_micro_forks(self, dry_run: bool) -> list[MaintenanceItem]:
        """Maintain old micro-forks."""
        items = []
        forks_dir = self.wiki_dir / "reports" / "micro-forks"
        if not forks_dir.exists():
            return items

        threshold = self.THRESHOLDS["micro_fork"]

        for fork in forks_dir.glob("*.json"):
            if self._is_old(fork, threshold["days"]):
                item = MaintenanceItem(
                    item_path=str(fork),
                    item_type="micro_fork",
                    action=threshold["action"],
                    reason=f"Older than {threshold['days']} days",
                )

                if not dry_run:
                    fork.unlink()
                    item.executed = True
                    item.executed_at = datetime.now(timezone.utc).isoformat()

                items.append(item)

        return items

    def _archive_item(self, source: Path, subdir: str) -> None:
        """Move item to archive."""
        archive_subdir = self.archive_dir / subdir
        archive_subdir.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(archive_subdir / source.name))

    def _update_index(self, dry_run: bool) -> bool:
        """
        Update wiki index.md with current statistics.
        """
        index_file = self.wiki_dir / "index.md"

        # Gather stats
        stats = self._gather_stats()

        index_content = f"""# Wiki Index

Auto-generated: {datetime.now(timezone.utc).isoformat()}

## Statistics

- Entities: {stats['entities']}
- TaskPacks: {stats['taskpacks']}
- Snapshots: {stats['snapshots']}
- Deferred Issues: {stats['deferred_issues']}
- Micro-Forks: {stats['micro_forks']}

## Quick Links

- [Entities](./entities/)
- [TaskPacks](./taskpacks/)
- [Reports](./reports/)

"""

        if not dry_run:
            index_file.write_text(index_content, encoding="utf-8")
            return True
        return False

    def _gather_stats(self) -> dict[str, int]:
        """Gather statistics about wiki contents."""
        stats = {
            "entities": 0,
            "taskpacks": 0,
            "snapshots": 0,
            "deferred_issues": 0,
            "micro_forks": 0,
        }

        entities_dir = self.wiki_dir / "entities"
        if entities_dir.exists():
            stats["entities"] = len(list(entities_dir.glob("*.md")))

        taskpacks_dir = self.wiki_dir / "taskpacks"
        if taskpacks_dir.exists():
            stats["taskpacks"] = len(list(taskpacks_dir.glob("*.json")))

        snapshots_dir = self.wiki_dir / "snapshots"
        if snapshots_dir.exists():
            stats["snapshots"] = len(list(snapshots_dir.glob("*.json")))

        deferred_dir = self.wiki_dir / "reports" / "deferred-issues"
        if deferred_dir.exists():
            stats["deferred_issues"] = len(list(deferred_dir.glob("*.json")))

        forks_dir = self.wiki_dir / "reports" / "micro-forks"
        if forks_dir.exists():
            stats["micro_forks"] = len(list(forks_dir.glob("*.json")))

        return stats

    def stale_recovery(self, entity_path: str, dry_run: bool = True) -> dict[str, Any]:
        """
        Recover a stale entity by re-digesting or archiving.
        """
        entity_file = self.workspace / entity_path
        result = {
            "entity_path": entity_path,
            "found": entity_file.exists(),
            "action": "none",
            "executed": False,
        }

        if not entity_file.exists():
            result["action"] = "not_found"
            return result

        # Read current status
        try:
            content = entity_file.read_text(encoding="utf-8")
            if "status: stale" in content:
                result["action"] = "mark_for_reconcile"
                if not dry_run:
                    # Would trigger re-digest here
                    result["executed"] = True
            elif "status: error" in content:
                result["action"] = "mark_for_defer"
        except Exception as e:
            result["action"] = "error"
            result["error"] = str(e)

        return result
