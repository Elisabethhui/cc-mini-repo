"""
Query Archive module (Phase 5)
Provides query capabilities for archived items.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator


@dataclass
class QueryResult:
    """Query result item"""
    archive_path: str
    original_path: str
    item_type: str
    archived_at: str
    reason: str
    size_bytes: int


class QueryArchive:
    """
    Phase 5: Query archive for historical snapshots, taskpacks, and reports.
    """

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root).resolve()
        self.archive_dir = self.workspace / ".cc-mini" / "wiki" / "archive"
        self.manifest_path = self.archive_dir / "manifest.json"

    def _load_manifest(self) -> list[dict[str, Any]]:
        """Load archive manifest"""
        if not self.manifest_path.exists():
            return []
        try:
            return json.loads(self.manifest_path.read_text())
        except Exception:
            return []

    def query_by_type(self, item_type: str) -> list[QueryResult]:
        """
        Query archived items by type.
        item_type: snapshot, taskpack, report, entity
        """
        manifest = self._load_manifest()
        results = []

        for entry in manifest:
            if entry.get("item_type") == item_type:
                results.append(QueryResult(
                    archive_path=entry.get("archive_path", ""),
                    original_path=entry.get("original_path", ""),
                    item_type=entry.get("item_type", ""),
                    archived_at=entry.get("archived_at", ""),
                    reason=entry.get("reason", ""),
                    size_bytes=entry.get("size_bytes", 0),
                ))

        return results

    def query_by_date_range(
        self,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> list[QueryResult]:
        """
        Query archived items by date range.
        Dates should be in ISO format (YYYY-MM-DD).
        """
        manifest = self._load_manifest()
        results = []

        for entry in manifest:
            archived_at = entry.get("archived_at", "")
            if not archived_at:
                continue

            # Compare dates
            if start_date and archived_at < start_date:
                continue
            if end_date and archived_at > end_date:
                continue

            results.append(QueryResult(
                archive_path=entry.get("archive_path", ""),
                original_path=entry.get("original_path", ""),
                item_type=entry.get("item_type", ""),
                archived_at=archived_at,
                reason=entry.get("reason", ""),
                size_bytes=entry.get("size_bytes", 0),
            ))

        return results

    def query_by_original_path(self, original_path: str) -> list[QueryResult]:
        """
        Query archived items by original path (fuzzy match).
        """
        manifest = self._load_manifest()
        results = []

        for entry in manifest:
            if original_path in entry.get("original_path", ""):
                results.append(QueryResult(
                    archive_path=entry.get("archive_path", ""),
                    original_path=entry.get("original_path", ""),
                    item_type=entry.get("item_type", ""),
                    archived_at=entry.get("archived_at", ""),
                    reason=entry.get("reason", ""),
                    size_bytes=entry.get("size_bytes", 0),
                ))

        return results

    def get_latest(self, item_type: str) -> QueryResult | None:
        """
        Get the most recently archived item of a given type.
        """
        results = self.query_by_type(item_type)
        if not results:
            return None

        # Sort by archived_at descending
        results.sort(key=lambda r: r.archived_at, reverse=True)
        return results[0]

    def search(self, keyword: str) -> list[QueryResult]:
        """
        Search archived items by keyword (searches paths).
        """
        manifest = self._load_manifest()
        results = []
        keyword = keyword.lower()

        for entry in manifest:
            searchable = f"{entry.get('original_path', '')} {entry.get('archive_path', '')}".lower()
            if keyword in searchable:
                results.append(QueryResult(
                    archive_path=entry.get("archive_path", ""),
                    original_path=entry.get("original_path", ""),
                    item_type=entry.get("item_type", ""),
                    archived_at=entry.get("archived_at", ""),
                    reason=entry.get("reason", ""),
                    size_bytes=entry.get("size_bytes", 0),
                ))

        return results

    def list_all(self, limit: int = 100) -> list[QueryResult]:
        """
        List all archived items (most recent first).
        """
        manifest = self._load_manifest()
        results = []

        for entry in sorted(manifest, key=lambda e: e.get("archived_at", ""), reverse=True)[:limit]:
            results.append(QueryResult(
                archive_path=entry.get("archive_path", ""),
                original_path=entry.get("original_path", ""),
                item_type=entry.get("item_type", ""),
                archived_at=entry.get("archived_at", ""),
                reason=entry.get("reason", ""),
                size_bytes=entry.get("size_bytes", 0),
            ))

        return results

    def get_summary(self) -> dict[str, Any]:
        """
        Get summary statistics of archived items.
        """
        manifest = self._load_manifest()

        total_items = len(manifest)
        by_type: dict[str, int] = {}
        total_size = 0

        for entry in manifest:
            item_type = entry.get("item_type", "unknown")
            by_type[item_type] = by_type.get(item_type, 0) + 1
            total_size += entry.get("size_bytes", 0)

        return {
            "total_items": total_items,
            "total_size_bytes": total_size,
            "by_type": by_type,
        }
