"""
Archive module (Phase 5)
Handles archiving of old snapshots, taskpacks, and reports.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any


@dataclass
class ArchiveItem:
    """Archived item metadata"""
    original_path: str = ""
    archive_path: str = ""
    archived_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    item_type: str = ""           # snapshot, taskpack, report, entity
    reason: str = ""              # age, manual, reconcile
    size_bytes: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "original_path": self.original_path,
            "archive_path": self.archive_path,
            "archived_at": self.archived_at,
            "item_type": self.item_type,
            "reason": self.reason,
            "size_bytes": self.size_bytes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArchiveItem:
        return cls(
            original_path=data.get("original_path", ""),
            archive_path=data.get("archive_path", ""),
            archived_at=data.get("archived_at", ""),
            item_type=data.get("item_type", ""),
            reason=data.get("reason", ""),
            size_bytes=data.get("size_bytes", 0),
        )


class ArchiveEngine:
    """
    Phase 5: Archive engine for old snapshots, taskpacks, and reports.
    """

    # Default age thresholds for auto-archive
    DEFAULT_AGE_DAYS = {
        "snapshot": 7,        # 7 days
        "taskpack": 30,       # 30 days
        "report": 14,         # 14 days
        "entity": 90,         # 90 days
    }

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root).resolve(strict=False)
        self.wiki_dir = self.workspace / ".cc-mini" / "wiki"
        self.archive_dir = self.wiki_dir / "archive"
        self.manifest_path = self.archive_dir / "manifest.json"

        # Create archive subdirectories
        for subdir in ["snapshots", "taskpacks", "reports", "entities"]:
            (self.archive_dir / subdir).mkdir(parents=True, exist_ok=True)

    def archive_item(
        self,
        source_path: str | Path,
        item_type: str,
        reason: str = "manual",
    ) -> ArchiveItem:
        """
        Archive a single item.
        """
        source = Path(source_path)
        if not source.exists():
            raise FileNotFoundError(f"Source not found: {source}")

        # Determine archive destination
        type_dir = self.archive_dir / item_type
        type_dir.mkdir(exist_ok=True)

        # Generate archive filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_name = f"{source.stem}.{timestamp}{source.suffix}"
        archive_path = type_dir / archive_name

        # Move or copy
        if source.is_file():
            shutil.copy2(source, archive_path)
            size = archive_path.stat().st_size
        elif source.is_dir():
            shutil.copytree(source, archive_path)
            size = sum(f.stat().st_size for f in archive_path.rglob("*") if f.is_file())
        else:
            size = 0

        # Handle potential symlink resolution issues
        try:
            original_rel = str(source.relative_to(self.workspace))
        except ValueError:
            original_rel = str(source)
        try:
            archive_rel = str(archive_path.relative_to(self.workspace))
        except ValueError:
            archive_rel = str(archive_path)

        item = ArchiveItem(
            original_path=original_rel,
            archive_path=archive_rel,
            item_type=item_type,
            reason=reason,
            size_bytes=size,
        )

        self._update_manifest(item)
        return item

    def auto_archive(self, dry_run: bool = False) -> list[ArchiveItem]:
        """
        Auto-archive old items based on age thresholds.
        """
        archived = []

        # Check snapshots
        snapshots_dir = self.wiki_dir / "snapshots"
        if snapshots_dir.exists():
            for snapshot in snapshots_dir.glob("*.json"):
                if self._is_old(snapshot, self.DEFAULT_AGE_DAYS["snapshot"]):
                    if not dry_run:
                        item = self.archive_item(snapshot, "snapshot", reason="age")
                        archived.append(item)
                    else:
                        archived.append(ArchiveItem(
                            original_path=str(snapshot),
                            item_type="snapshot",
                            reason="age (dry_run)",
                        ))

        # Check old taskpacks
        taskpacks_dir = self.wiki_dir / "taskpacks"
        if taskpacks_dir.exists():
            for taskpack in taskpacks_dir.glob("*.json"):
                if self._is_old(taskpack, self.DEFAULT_AGE_DAYS["taskpack"]):
                    if not dry_run:
                        item = self.archive_item(taskpack, "taskpack", reason="age")
                        archived.append(item)
                    else:
                        archived.append(ArchiveItem(
                            original_path=str(taskpack),
                            item_type="taskpack",
                            reason="age (dry_run)",
                        ))

        return archived

    def _is_old(self, path: Path, days: int) -> bool:
        """Check if file is older than specified days"""
        if not path.exists():
            return False
        mtime = datetime.fromtimestamp(path.stat().st_mtime, timezone.utc)
        return datetime.now(timezone.utc) - mtime > timedelta(days=days)

    def _update_manifest(self, item: ArchiveItem) -> None:
        """Update archive manifest"""
        manifest = []
        if self.manifest_path.exists():
            try:
                manifest = json.loads(self.manifest_path.read_text())
            except Exception:
                pass

        manifest.append(item.to_dict())
        self.manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    def get_stats(self) -> dict[str, Any]:
        """Get archive statistics"""
        stats = {
            "total_items": 0,
            "total_size_bytes": 0,
            "by_type": {},
        }

        if not self.manifest_path.exists():
            return stats

        try:
            manifest = json.loads(self.manifest_path.read_text())
            for entry in manifest:
                stats["total_items"] += 1
                stats["total_size_bytes"] += entry.get("size_bytes", 0)

                item_type = entry.get("item_type", "unknown")
                if item_type not in stats["by_type"]:
                    stats["by_type"][item_type] = {"count": 0, "size_bytes": 0}
                stats["by_type"][item_type]["count"] += 1
                stats["by_type"][item_type]["size_bytes"] += entry.get("size_bytes", 0)
        except Exception:
            pass

        return stats
