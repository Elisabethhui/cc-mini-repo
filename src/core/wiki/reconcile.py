"""
Reconcile module (Phase 3 projections)
Handles stale/drift/digest expired pages reconciliation and read-only projections.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from enum import Enum

from .semantic_artifacts import SemanticArtifactStore


class ReconcileAction(str, Enum):
    """Possible reconcile actions"""
    RE_DIGEST = "re_digest"           # Re-run digest
    ARCHIVE = "archive"               # Archive old version
    UPDATE = "update"                 # Update metadata only
    DEFER = "defer"                   # Defer to manual handling
    DELETE = "delete"                 # Delete orphaned entity


@dataclass
class ReconcileItem:
    """Single item needing reconciliation"""
    entity_path: str = ""
    current_status: str = ""          # stale, drifted, expired, etc.
    detected_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    reason: str = ""
    suggested_action: ReconcileAction = ReconcileAction.DEFER
    applied: bool = False
    applied_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_path": self.entity_path,
            "current_status": self.current_status,
            "detected_at": self.detected_at,
            "reason": self.reason,
            "suggested_action": self.suggested_action.value,
            "applied": self.applied,
            "applied_at": self.applied_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ReconcileItem:
        return cls(
            entity_path=data.get("entity_path", ""),
            current_status=data.get("current_status", ""),
            detected_at=data.get("detected_at", ""),
            reason=data.get("reason", ""),
            suggested_action=ReconcileAction(data.get("suggested_action", "defer")),
            applied=data.get("applied", False),
            applied_at=data.get("applied_at"),
        )


class ReconcileEngine:
    """
    Phase 5: Reconcile engine for stale/drift/digest expired pages.
    """

    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root).resolve()
        self.wiki_dir = self.workspace / ".cc-mini" / "wiki"
        self.entities_dir = self.wiki_dir / "entities"
        self.reports_dir = self.wiki_dir / "reports"
        self.reconcile_log = self.reports_dir / "reconcile_log.json"

        # Ensure directories exist
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def scan_for_stale(self) -> list[ReconcileItem]:
        """
        Scan entities directory for stale entries.
        Returns list of items needing reconciliation.
        """
        items = []

        if not self.entities_dir.exists():
            return items

        for entity_file in self.entities_dir.glob("*.md"):
            try:
                content = entity_file.read_text(encoding="utf-8")
                status = self._extract_status(content)

                if status == "stale":
                    items.append(ReconcileItem(
                        entity_path=str(entity_file.relative_to(self.workspace)),
                        current_status="stale",
                        reason="Entity marked as stale - source file changed",
                        suggested_action=ReconcileAction.RE_DIGEST,
                    ))
                elif status == "error":
                    items.append(ReconcileItem(
                        entity_path=str(entity_file.relative_to(self.workspace)),
                        current_status="error",
                        reason="Entity has error status - parse failed",
                        suggested_action=ReconcileAction.DEFER,
                    ))

            except Exception as e:
                items.append(ReconcileItem(
                    entity_path=str(entity_file.relative_to(self.workspace)),
                    current_status="error",
                    reason=f"Failed to read entity: {e}",
                    suggested_action=ReconcileAction.DEFER,
                ))

        return items

    def _extract_status(self, content: str) -> str | None:
        """Extract status from entity frontmatter"""
        import re
        match = re.search(r'^status:\s*(\w+)', content, re.MULTILINE)
        return match.group(1) if match else None

    def check_source_drift(self, entity_path: str) -> tuple[bool, str]:
        """
        Check if source file has drifted from entity.
        Returns (has_drifted, reason)
        """
        entity_file = self.workspace / entity_path
        if not entity_file.exists():
            return True, "Entity file not found"

        # Try to find corresponding source file
        # Assuming entity name is {source_file}.md
        entity_name = entity_file.stem  # e.g., "test.py" from "test.py.md"
        source_candidates = [
            self.workspace / entity_name,
            self.workspace / "src" / entity_name,
        ]

        source_file = None
        for candidate in source_candidates:
            if candidate.exists():
                source_file = candidate
                break

        if not source_file:
            return True, f"Source file not found for {entity_name}"

        # Read entity source_hash
        entity_content = entity_file.read_text(encoding="utf-8")
        import re
        hash_match = re.search(r'^source_hash:\s*([a-f0-9]+)', entity_content, re.MULTILINE)
        if not hash_match:
            return True, "No source_hash in entity"

        stored_hash = hash_match.group(1)

        # Compute current hash
        import hashlib
        current_content = source_file.read_text(encoding="utf-8")
        current_hash = hashlib.sha256(current_content.encode("utf-8")).hexdigest()[:16]

        if stored_hash != current_hash:
            return True, f"Source hash mismatch: stored={stored_hash}, current={current_hash}"

        return False, "Source matches entity"

    def reconcile(self, dry_run: bool = False) -> dict[str, Any]:
        """
        Main reconcile entry point.
        Scans for stale entities and generates reconcile items.
        """
        items = self.scan_for_stale()
        artifact_projection = self.project_artifact_reconcile()
        items.extend(artifact_projection["items"])

        # Check for source drift on non-stale entities
        if self.entities_dir.exists():
            for entity_file in self.entities_dir.glob("*.md"):
                entity_path = str(entity_file.relative_to(self.workspace))
                has_drifted, reason = self.check_source_drift(entity_path)

                if has_drifted and not any(i.entity_path == entity_path for i in items):
                    items.append(ReconcileItem(
                        entity_path=entity_path,
                        current_status="drifted",
                        reason=reason,
                        suggested_action=ReconcileAction.RE_DIGEST,
                    ))

        # Log reconcile run
        result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "items_found": len(items),
            "items": [item.to_dict() for item in items],
            "artifact_projection": {
                "derived_count": artifact_projection["derived_count"],
                "manual_count": artifact_projection["manual_count"],
                "items": [item.to_dict() for item in artifact_projection["items"]],
            },
            "dry_run": dry_run,
        }

        if not dry_run:
            self._save_reconcile_log(result)

        return result

    def _save_reconcile_log(self, result: dict[str, Any]) -> None:
        """Append reconcile result to log"""
        logs = []
        if self.reconcile_log.exists():
            try:
                logs = json.loads(self.reconcile_log.read_text())
            except Exception:
                pass

        logs.append(result)
        self.reconcile_log.write_text(json.dumps(logs, indent=2), encoding="utf-8")

    def project_artifact_reconcile(self) -> dict[str, Any]:
        """
        Build a read-only reconcile projection from semantic artifacts.
        """
        store = SemanticArtifactStore(self.workspace)
        items: list[ReconcileItem] = []
        derived_count = 0
        manual_count = 0

        for record in store.list_layer("derived"):
            derived_count += 1
            if record.kind in {"drift_note", "maintenance_candidate"}:
                items.append(ReconcileItem(
                    entity_path=f".cc-mini/wiki/artifacts/derived/{record.artifact_id}.json",
                    current_status=record.kind,
                    reason=f"Derived artifact projection for {record.task_id}",
                    suggested_action=ReconcileAction.DEFER,
                ))

        for record in store.list_layer("manual"):
            manual_count += 1
            items.append(ReconcileItem(
                entity_path=f".cc-mini/wiki/artifacts/manual/{record.artifact_id}.json",
                current_status="manual_annotation",
                reason=f"Manual artifact projection for {record.task_id}: {record.kind}",
                suggested_action=ReconcileAction.DEFER,
            ))

        return {
            "derived_count": derived_count,
            "manual_count": manual_count,
            "items": items,
        }

    def apply_action(self, entity_path: str, action: ReconcileAction) -> dict[str, Any]:
        """
        Apply a reconcile action to an entity.
        """
        result = {
            "entity_path": entity_path,
            "action": action.value,
            "applied": False,
            "message": "",
        }

        entity_file = self.workspace / entity_path

        if action == ReconcileAction.RE_DIGEST:
            # Trigger re-digest (would call ingester in real implementation)
            result["message"] = f"Re-digest triggered for {entity_path}"
            result["applied"] = True

        elif action == ReconcileAction.ARCHIVE:
            # Move to archive
            archive_dir = self.wiki_dir / "archive" / "entities"
            archive_dir.mkdir(parents=True, exist_ok=True)

            if entity_file.exists():
                import shutil
                shutil.move(str(entity_file), str(archive_dir / entity_file.name))
                result["message"] = f"Archived to {archive_dir / entity_file.name}"
                result["applied"] = True
            else:
                result["message"] = "Entity file not found"

        elif action == ReconcileAction.DELETE:
            # Delete orphaned entity
            if entity_file.exists():
                entity_file.unlink()
                result["message"] = f"Deleted {entity_path}"
                result["applied"] = True
            else:
                result["message"] = "Entity file not found"

        elif action == ReconcileAction.DEFER:
            result["message"] = f"Deferred {entity_path} for manual handling"
            result["applied"] = True

        else:
            result["message"] = f"Action {action.value} not yet implemented"

        return result
