from __future__ import annotations

import json

import pytest

from core.dev_contract import TaskResult
from core.runtime_state import RuntimeStateStore
from core.step_artifact_store import StepArtifactStore


def _make_store(tmp_path):
    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    return StepArtifactStore(workspace=tmp_path, runtime_store=runtime_store)


# ---------------------------------------------------------------------------
# Recording and indexing
# ---------------------------------------------------------------------------

def test_record_step_writes_index(tmp_path):
    store = _make_store(tmp_path)
    artifacts_dir = store._artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    path1 = artifacts_dir / "step-001-prompt.md"
    path1.write_text("prompt", encoding="utf-8")

    store.record_step(
        task_id="task-001",
        step_id="step-001",
        artifact_paths=[path1],
        task_result=TaskResult(task_id="task-001", status="passed"),
    )

    assert store._step_index_path.exists()
    data = json.loads(store._step_index_path.read_text(encoding="utf-8"))
    assert len(data["steps"]) == 1
    assert data["steps"][0]["task_id"] == "task-001"
    assert data["steps"][0]["step_id"] == "step-001"
    assert data["steps"][0]["status"] == "passed"


def test_list_steps_filters_by_task_id(tmp_path):
    store = _make_store(tmp_path)
    artifacts_dir = store._artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    path_a = artifacts_dir / "step-a-prompt.md"
    path_b = artifacts_dir / "step-b-prompt.md"
    path_a.write_text("a", encoding="utf-8")
    path_b.write_text("b", encoding="utf-8")

    store.record_step("task-001", "step-a", [path_a])
    store.record_step("task-002", "step-b", [path_b])

    steps = store.list_steps("task-001")
    assert len(steps) == 1
    assert steps[0]["step_id"] == "step-a"


def test_list_steps_all(tmp_path):
    store = _make_store(tmp_path)
    artifacts_dir = store._artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    path_a = artifacts_dir / "step-a-prompt.md"
    path_b = artifacts_dir / "step-b-prompt.md"
    path_a.write_text("a", encoding="utf-8")
    path_b.write_text("b", encoding="utf-8")

    store.record_step("task-001", "step-a", [path_a])
    store.record_step("task-002", "step-b", [path_b])

    steps = store.list_steps()
    assert len(steps) == 2


def test_latest_step_returns_most_recent(tmp_path):
    store = _make_store(tmp_path)
    artifacts_dir = store._artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    for step_id in ("step-001", "step-002"):
        path = artifacts_dir / f"{step_id}-prompt.md"
        path.write_text("x", encoding="utf-8")
        store.record_step("task-001", step_id, [path])

    latest = store.latest_step("task-001")
    assert latest is not None
    assert latest["step_id"] == "step-002"


def test_latest_step_missing_returns_none(tmp_path):
    store = _make_store(tmp_path)
    assert store.latest_step("task-001") is None


# ---------------------------------------------------------------------------
# Artifact validation
# ---------------------------------------------------------------------------

def test_validate_expected_artifacts_all_present(tmp_path):
    store = _make_store(tmp_path)
    artifacts_dir = store._artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    names = [
        "step-001-prompt.md",
        "step-001-engine-events.json",
        "step-001-verification-result.json",
        "step-001-step-result.json",
        "step-001-task-result.json",
    ]
    for name in names:
        (artifacts_dir / name).write_text("{}", encoding="utf-8")

    ok, missing = store.validate_expected_artifacts("step-001")
    assert ok is True
    assert missing == []


def test_validate_expected_artifacts_reports_missing(tmp_path):
    store = _make_store(tmp_path)
    artifacts_dir = store._artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    (artifacts_dir / "step-001-step-result.json").write_text("{}", encoding="utf-8")

    ok, missing = store.validate_expected_artifacts("step-001")
    assert ok is False
    assert "step-001-prompt.md" in missing
    assert "step-001-task-result.json" in missing


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def test_load_step_result(tmp_path):
    store = _make_store(tmp_path)
    artifacts_dir = store._artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "step_id": "step-001",
        "task_id": "task-001",
        "status": "passed",
    }
    (artifacts_dir / "step-001-step-result.json").write_text(
        json.dumps(data), encoding="utf-8"
    )

    result = store.load_step_result("step-001")
    assert result is not None
    assert result.step_id == "step-001"
    assert result.status == "passed"


def test_load_step_result_missing_returns_none(tmp_path):
    store = _make_store(tmp_path)
    assert store.load_step_result("step-001") is None


def test_load_verification_result(tmp_path):
    store = _make_store(tmp_path)
    artifacts_dir = store._artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "kind": "command",
        "command": ["echo", "ok"],
        "passed": True,
        "exit_code": 0,
    }
    (artifacts_dir / "step-001-verification-result.json").write_text(
        json.dumps(data), encoding="utf-8"
    )

    result = store.load_verification_result("step-001")
    assert result is not None
    assert result.kind == "command"
    assert result.passed is True


def test_load_task_result_from_step(tmp_path):
    store = _make_store(tmp_path)
    artifacts_dir = store._artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "task_id": "task-001",
        "status": "passed",
        "verification_passed": True,
    }
    (artifacts_dir / "step-001-task-result.json").write_text(
        json.dumps(data), encoding="utf-8"
    )

    result = store.load_task_result_from_step("step-001")
    assert result is not None
    assert result.task_id == "task-001"
    assert result.status == "passed"


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------

def test_record_step_rejects_outside_runtime_path(tmp_path):
    store = _make_store(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError):
        store.record_step("task-001", "step-001", [outside])


def test_index_uses_relative_paths(tmp_path):
    store = _make_store(tmp_path)
    artifacts_dir = store._artifacts_dir
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    path = artifacts_dir / "step-001-prompt.md"
    path.write_text("prompt", encoding="utf-8")

    store.record_step("task-001", "step-001", [path])

    data = json.loads(store._step_index_path.read_text(encoding="utf-8"))
    rel_paths = data["steps"][0]["artifact_paths"]
    assert rel_paths
    for p in rel_paths:
        assert not p.startswith("/")
        assert ".." not in p


@pytest.mark.parametrize(
    "bad_id",
    [
        "../task",
        "/tmp/task",
        ".git/config",
        "",
        "a/b",
    ],
)
def test_invalid_task_id_rejected(tmp_path, bad_id):
    store = _make_store(tmp_path)
    with pytest.raises(ValueError):
        store.list_steps(bad_id)
    with pytest.raises(ValueError):
        store.latest_step(bad_id)
