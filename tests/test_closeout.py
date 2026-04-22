from __future__ import annotations

import json


def test_closeout_record_round_trip(tmp_path):
    from core.wiki.closeout import CloseoutRecord, CloseoutStore

    store = CloseoutStore(tmp_path)
    record = CloseoutRecord(
        task_id="task-1",
        phase_name="Phase 6",
        verification_status="passed",
        review_status="approved",
        commit_status="pending",
        commit_hash=None,
        ready_for_audit=False,
        residual_risks=["commit confirmation still pending"],
    )

    path = store.save(record)
    restored = store.load(path.stem)

    assert restored.task_id == "task-1"
    assert restored.phase_name == "Phase 6"
    assert restored.verification_status == "passed"
    assert restored.review_status == "approved"
    assert restored.commit_status == "pending"
    assert restored.commit_hash is None
    assert restored.ready_for_audit is False
    assert restored.residual_risks == ["commit confirmation still pending"]
    assert restored.created_at
    assert restored.updated_at

    md_path = path.with_suffix(".md")
    assert path.exists()
    assert md_path.exists()
    assert "commit confirmation" in store.render_markdown(restored)
    assert "commit confirmation" in md_path.read_text(encoding="utf-8")

    json_payload = json.loads(path.read_text(encoding="utf-8"))
    assert json_payload["task_id"] == "task-1"
    assert json_payload["phase_name"] == "Phase 6"


def test_closeout_store_load_latest_supports_task_filter(tmp_path):
    from core.wiki.closeout import CloseoutRecord, CloseoutStore

    store = CloseoutStore(tmp_path)

    first = store.save(
        CloseoutRecord(
            task_id="task-1",
            phase_name="Phase 6",
            verification_status="passed",
            review_status="approved",
            commit_status="pending",
            commit_hash=None,
            ready_for_audit=False,
            residual_risks=[],
        )
    )
    second = store.save(
        CloseoutRecord(
            task_id="task-2",
            phase_name="Phase 6",
            verification_status="passed",
            review_status="approved",
            commit_status="recorded",
            commit_hash="abc1234",
            ready_for_audit=True,
            residual_risks=[],
        )
    )

    latest = store.load_latest()
    latest_for_task = store.load_latest(task_id="task-1")

    assert first.suffix == ".json"
    assert second.suffix == ".json"
    assert latest is not None
    assert latest.task_id == "task-2"
    assert latest_for_task is not None
    assert latest_for_task.task_id == "task-1"
    assert first.with_suffix(".md").exists()
    assert second.with_suffix(".md").exists()
