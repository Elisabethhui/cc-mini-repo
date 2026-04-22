"""
Workspace semantic artifact storage for Phase 3.

This module stores workspace-level semantic records in two explicit strata:
`derived` artifacts produced from workflow output and `manual` artifacts
authored by the user. The store is intentionally read/write only for these
records and does not touch source files.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ALLOWED_LAYERS = {"derived", "manual"}


@dataclass
class ArtifactRecord:
    artifact_id: str
    layer: str
    kind: str
    task_id: str
    source: str
    priority: int
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    payload: dict[str, Any] = field(default_factory=dict)
    references: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.layer not in ALLOWED_LAYERS:
            raise ValueError(f"Unsupported artifact layer: {self.layer}")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ArtifactRecord:
        return cls(**data)


class SemanticArtifactStore:
    def __init__(self, workspace_root: str | Path):
        self.workspace = Path(workspace_root).resolve()
        self.artifacts_root = self.workspace / ".cc-mini" / "wiki" / "artifacts"
        self.derived_dir = self.artifacts_root / "derived"
        self.manual_dir = self.artifacts_root / "manual"
        self.index_file = self.artifacts_root / "index.json"
        self.derived_dir.mkdir(parents=True, exist_ok=True)
        self.manual_dir.mkdir(parents=True, exist_ok=True)
        self._index = self._load_index()

    def save(self, record: ArtifactRecord) -> Path:
        record.updated_at = datetime.now(timezone.utc).isoformat()
        path = self._artifact_path(record.layer, record.artifact_id)
        path.write_text(json.dumps(record.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        self._upsert_index(record, path)
        self._write_index()
        return path

    def load(self, layer: str, artifact_id: str) -> ArtifactRecord:
        path = self._artifact_path(layer, artifact_id)
        data = json.loads(path.read_text(encoding="utf-8"))
        return ArtifactRecord.from_dict(data)

    def list_layer(self, layer: str) -> list[ArtifactRecord]:
        if layer not in ALLOWED_LAYERS:
            raise ValueError(f"Unsupported artifact layer: {layer}")
        layer_entries = self._index.get(layer, {})
        records: list[ArtifactRecord] = []
        for artifact_id in sorted(layer_entries):
            records.append(self.load(layer, artifact_id))
        return records

    def list_for_task(self, task_id: str) -> list[ArtifactRecord]:
        records: list[ArtifactRecord] = []
        for layer in sorted(ALLOWED_LAYERS):
            for record in self.list_layer(layer):
                if record.task_id == task_id:
                    records.append(record)
        records.sort(key=lambda item: (item.priority, item.created_at), reverse=True)
        return records

    def ingest_convergence_record(self, record: dict[str, Any]) -> list[ArtifactRecord]:
        required_fields = {"task_id", "confirmed", "summary", "references"}
        missing = sorted(required_fields.difference(record))
        if missing:
            raise ValueError(f"Missing convergence record fields: {', '.join(missing)}")

        task_id = str(record["task_id"])
        references = list(record.get("references", []))
        confirmed = bool(record["confirmed"])
        summary = record["summary"]

        convergence = ArtifactRecord(
            artifact_id=f"{task_id}-convergence-record",
            layer="derived",
            kind="convergence_record",
            task_id=task_id,
            source="phase2",
            priority=100,
            payload={
                "confirmed": confirmed,
                "summary": summary,
                "references": references,
            },
            references=references,
        )
        task_spine = ArtifactRecord(
            artifact_id=f"{task_id}-task-spine",
            layer="derived",
            kind="task_spine",
            task_id=task_id,
            source="phase2",
            priority=90,
            payload={
                "task_id": task_id,
                "confirmed": confirmed,
                "summary": summary,
                "references": references,
            },
            references=references,
        )

        self.save(convergence)
        self.save(task_spine)
        return [convergence, task_spine]

    def add_manual_annotation(
        self,
        task_id: str,
        note: str,
        kind: str = "annotation",
        references: list[str] | None = None,
    ) -> ArtifactRecord:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
        record = ArtifactRecord(
            artifact_id=f"{task_id}-manual-{timestamp}",
            layer="manual",
            kind=kind,
            task_id=task_id,
            source="user",
            priority=1,
            payload={"note": note},
            references=list(references or []),
        )
        self.save(record)
        return record

    def _artifact_path(self, layer: str, artifact_id: str) -> Path:
        if layer not in ALLOWED_LAYERS:
            raise ValueError(f"Unsupported artifact layer: {layer}")
        return (self.derived_dir if layer == "derived" else self.manual_dir) / f"{artifact_id}.json"

    def _load_index(self) -> dict[str, dict[str, dict[str, Any]]]:
        if not self.index_file.exists():
            return {"derived": {}, "manual": {}}
        try:
            data = json.loads(self.index_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"derived": {}, "manual": {}}
        index = {"derived": {}, "manual": {}}
        for layer in ALLOWED_LAYERS:
            layer_entries = data.get(layer, {})
            if isinstance(layer_entries, dict):
                index[layer] = layer_entries
        return index

    def _write_index(self) -> None:
        self.index_file.write_text(json.dumps(self._index, ensure_ascii=False, indent=2), encoding="utf-8")

    def _upsert_index(self, record: ArtifactRecord, path: Path) -> None:
        self._index.setdefault(record.layer, {})
        self._index[record.layer][record.artifact_id] = {
            "artifact_id": record.artifact_id,
            "layer": record.layer,
            "kind": record.kind,
            "task_id": record.task_id,
            "source": record.source,
            "priority": record.priority,
            "path": str(path.relative_to(self.workspace)),
            "created_at": record.created_at,
            "updated_at": record.updated_at,
            "references": record.references,
        }
