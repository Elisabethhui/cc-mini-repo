from __future__ import annotations

from core.wiki.maintenance import MaintenanceEngine
from core.wiki.reconcile import ReconcileEngine
from core.wiki.semantic_artifacts import ArtifactRecord, SemanticArtifactStore


def test_reconcile_uses_artifact_projection_without_writes(tmp_path):
    store = SemanticArtifactStore(tmp_path)
    store.save(
        ArtifactRecord(
            artifact_id="drift-1",
            layer="derived",
            kind="drift_note",
            task_id="task-1",
            source="phase3",
            priority=5,
            payload={"note": "entity drifted"},
        )
    )
    engine = ReconcileEngine(tmp_path)

    result = engine.reconcile(dry_run=True)

    assert result["dry_run"] is True
    assert result["artifact_projection"]["derived_count"] == 1
    assert result["items"]


def test_maintenance_projects_artifacts_without_writes(tmp_path):
    store = SemanticArtifactStore(tmp_path)
    store.save(
        ArtifactRecord(
            artifact_id="maint-1",
            layer="derived",
            kind="maintenance_candidate",
            task_id="task-1",
            source="phase3",
            priority=5,
            payload={"reason": "stale semantic snapshot"},
        )
    )
    engine = MaintenanceEngine(tmp_path)

    result = engine.project_artifact_maintenance()

    assert result["derived_count"] == 1
    assert result["items"]

