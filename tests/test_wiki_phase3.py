from __future__ import annotations

from core.wiki.semantic_artifacts import ArtifactRecord, SemanticArtifactStore


def test_long_session_preserves_derived_and_manual_layers(tmp_path):
    store = SemanticArtifactStore(tmp_path)
    store.save(
        ArtifactRecord(
            artifact_id="conv-1",
            layer="derived",
            kind="task_spine",
            task_id="task-1",
            source="phase2",
            priority=10,
            payload={"step_goal": "recover"},
        )
    )
    store.add_manual_annotation(task_id="task-1", note="retain this path")

    records = store.list_for_task("task-1")
    assert {r.layer for r in records} == {"derived", "manual"}
    assert {r.task_id for r in records} == {"task-1"}

