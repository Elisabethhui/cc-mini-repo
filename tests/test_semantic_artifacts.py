from __future__ import annotations

from core.wiki.semantic_artifacts import ArtifactRecord, SemanticArtifactStore


def test_store_separates_layers(tmp_path):
    store = SemanticArtifactStore(tmp_path)

    derived = ArtifactRecord(
        artifact_id="conv-1",
        layer="derived",
        kind="convergence_record",
        task_id="task-1",
        source="phase2",
        priority=10,
        payload={"summary": "patch accepted"},
    )
    manual = ArtifactRecord(
        artifact_id="note-1",
        layer="manual",
        kind="annotation",
        task_id="task-1",
        source="user",
        priority=1,
        payload={"note": "double-check naming"},
    )

    store.save(derived)
    store.save(manual)

    assert store.load("derived", "conv-1").artifact_id == "conv-1"
    assert store.load("manual", "note-1").artifact_id == "note-1"


def test_ingest_convergence_record_creates_derived_snapshot(tmp_path):
    store = SemanticArtifactStore(tmp_path)
    record = {
        "task_id": "task-1",
        "confirmed": True,
        "summary": {"files": ["src/app.py"]},
        "references": ["src/app.py"],
    }

    artifacts = store.ingest_convergence_record(record)

    assert any(item.kind == "convergence_record" for item in artifacts)
    assert any(item.layer == "derived" for item in store.list_layer("derived"))


def test_manual_annotation_does_not_replace_derived(tmp_path):
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
    store.add_manual_annotation(
        task_id="task-1",
        note="prefer shorter step labels",
    )

    records = store.list_for_task("task-1")
    assert {r.layer for r in records} == {"derived", "manual"}
