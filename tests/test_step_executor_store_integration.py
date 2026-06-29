from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from core.dev_contract import TaskResult, TaskSpec, VerificationSpec
from core.runtime_state import RuntimeStateStore
from core.step_artifact_store import StepArtifactStore
from core.step_executor import StepExecutor
from core.task_spec_store import TaskSpecStore


class FakeEngine:
    def __init__(self, events=None, side_effect=None):
        self.events = events or [("text", "done")]
        self.side_effect = side_effect
        self.call_count = 0

    def submit(self, prompt):
        self.call_count += 1
        if self.side_effect:
            self.side_effect(prompt)
        for event in self.events:
            yield event


def _make_stores(tmp_path):
    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    step_store = StepArtifactStore(workspace=tmp_path, runtime_store=runtime_store)
    return runtime_store, task_store, step_store


def _make_executor(tmp_path, task_store=None, step_artifact_store=None):
    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    return StepExecutor(
        workspace=tmp_path,
        runtime_store=runtime_store,
        context_window=32768,
        task_store=task_store,
        step_artifact_store=step_artifact_store,
    )


def _make_spec(**overrides) -> TaskSpec:
    defaults = {
        "id": "t1",
        "goal": "Add module",
        "task_kind": "coding",
        "task_type": "create",
        "executable": True,
        "planning_required": False,
        "allowed_files": ["src/mod.py"],
        "forbidden_files": [],
        "context_budget": 8000,
        "verification": VerificationSpec(kind="command", command=["echo", "ok"]),
        "confidence": 0.8,
    }
    defaults.update(overrides)
    return TaskSpec(**defaults)


def _mock_git_clean(monkeypatch):
    import subprocess as sp
    original = sp.run

    def fake_run(*args, **kwargs):
        if args and isinstance(args[0], list) and args[0][:2] == ["git", "status"]:
            return type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
        return original(*args, **kwargs)

    monkeypatch.setattr("subprocess.run", fake_run)


# ---------------------------------------------------------------------------
# Full integration
# ---------------------------------------------------------------------------

def test_executor_with_stores_saves_spec_result_and_indexes_step(monkeypatch, tmp_path):
    runtime_store, task_store, step_store = _make_stores(tmp_path)
    executor = _make_executor(tmp_path, task_store=task_store, step_artifact_store=step_store)
    spec = _make_spec(id="task-001")
    _mock_git_clean(monkeypatch)

    result = executor.execute_task(spec, FakeEngine())

    assert result.status == "passed"
    assert executor.task_store is task_store
    assert executor.step_artifact_store is step_store

    # TaskSpec saved
    loaded_spec = task_store.load_task_spec("task-001")
    assert loaded_spec is not None
    assert loaded_spec.id == "task-001"

    # TaskResult saved
    loaded_result = task_store.load_task_result("task-001")
    assert loaded_result is not None
    assert loaded_result.status == "passed"

    # task-results-index updated
    results_index = json.loads(
        task_store._task_results_index_path.read_text(encoding="utf-8")
    )
    assert any(r["task_id"] == "task-001" for r in results_index["results"])

    # step-index updated
    steps = step_store.list_steps("task-001")
    assert len(steps) == 1
    assert steps[0]["task_id"] == "task-001"
    assert steps[0]["status"] == "passed"


def test_executor_without_stores_keeps_old_behavior(monkeypatch, tmp_path):
    executor = _make_executor(tmp_path)
    spec = _make_spec()
    _mock_git_clean(monkeypatch)

    result = executor.execute_task(spec, FakeEngine())

    assert result.status == "passed"
    # No stores attached
    assert executor.task_store is None
    assert executor.step_artifact_store is None


def test_executor_blocked_result_still_saved(tmp_path):
    runtime_store, task_store, step_store = _make_stores(tmp_path)
    executor = _make_executor(tmp_path, task_store=task_store, step_artifact_store=step_store)
    spec = _make_spec(id="task-001", executable=False)
    engine = FakeEngine()

    result = executor.execute_task(spec, engine)

    assert result.status == "blocked"
    assert engine.call_count == 0

    loaded_result = task_store.load_task_result("task-001")
    assert loaded_result is not None
    assert loaded_result.status == "blocked"

    steps = step_store.list_steps("task-001")
    assert len(steps) == 1
    assert steps[0]["status"] == "blocked"


def test_executor_planning_required_result_still_saved(tmp_path):
    runtime_store, task_store, step_store = _make_stores(tmp_path)
    executor = _make_executor(tmp_path, task_store=task_store, step_artifact_store=step_store)
    spec = _make_spec(id="task-001", planning_required=True)
    engine = FakeEngine()

    result = executor.execute_task(spec, engine)

    assert result.status == "blocked"
    assert engine.call_count == 0

    loaded_result = task_store.load_task_result("task-001")
    assert loaded_result is not None
    assert loaded_result.status == "blocked"


def test_executor_failed_verification_saved_in_store(monkeypatch, tmp_path):
    runtime_store, task_store, step_store = _make_stores(tmp_path)
    executor = _make_executor(tmp_path, task_store=task_store, step_artifact_store=step_store)
    spec = _make_spec(
        id="task-001",
        verification=VerificationSpec(
            kind="command",
            command=["python3", "-c", "import sys; sys.exit(1)"],
        ),
    )
    _mock_git_clean(monkeypatch)

    result = executor.execute_task(spec, FakeEngine())

    assert result.status == "failed"
    loaded_result = task_store.load_task_result("task-001")
    assert loaded_result is not None
    assert loaded_result.status == "failed"

    steps = step_store.list_steps("task-001")
    assert steps[0]["status"] == "failed"


def test_all_five_artifacts_validated_by_step_store(monkeypatch, tmp_path):
    runtime_store, task_store, step_store = _make_stores(tmp_path)
    executor = _make_executor(tmp_path, task_store=task_store, step_artifact_store=step_store)
    spec = _make_spec(id="task-001")
    _mock_git_clean(monkeypatch)

    result = executor.execute_task(spec, FakeEngine())

    assert result.status == "passed"

    latest = step_store.latest_step("task-001")
    assert latest is not None
    step_id = latest["step_id"]

    ok, missing = step_store.validate_expected_artifacts(step_id)
    assert ok is True
    assert missing == []


def test_changed_files_not_from_assistant_text(monkeypatch, tmp_path):
    runtime_store, task_store, step_store = _make_stores(tmp_path)
    executor = _make_executor(tmp_path, task_store=task_store, step_artifact_store=step_store)
    spec = _make_spec(id="task-001")
    engine = FakeEngine(events=[("text", "I changed src/fake.py")])
    _mock_git_clean(monkeypatch)

    result = executor.execute_task(spec, engine)

    assert "src/fake.py" not in result.changed_files
    loaded_result = task_store.load_task_result("task-001")
    assert loaded_result is not None
    assert "src/fake.py" not in loaded_result.changed_files


def test_no_business_keywords_in_execution_logic(monkeypatch, tmp_path):
    runtime_store, task_store, step_store = _make_stores(tmp_path)
    executor = _make_executor(tmp_path, task_store=task_store, step_artifact_store=step_store)
    spec = _make_spec(id="task-001", goal="Create Flask React CLI app")
    _mock_git_clean(monkeypatch)

    result = executor.execute_task(spec, FakeEngine())

    for f in result.changed_files:
        assert f not in ("app.py", "requirements.txt", "package.json", "App.jsx")

    loaded_spec = task_store.load_task_spec("task-001")
    assert loaded_spec.allowed_files == ["src/mod.py"]
    assert "Flask" not in loaded_spec.allowed_files
    assert "React" not in loaded_spec.allowed_files
