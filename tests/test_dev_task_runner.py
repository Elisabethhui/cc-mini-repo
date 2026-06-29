from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from core.dev_contract import TaskResult, TaskSpec, VerificationSpec
from core.dev_task_runner import DevRunResult, DevTaskRunner
from core.runtime_state import RuntimeStateStore
from core.step_artifact_store import StepArtifactStore
from core.step_executor import StepExecutor
from core.task_spec_store import TaskSpecStore


# ---------------------------------------------------------------------------
# Fake engine helpers
# ---------------------------------------------------------------------------

class FakeEngine:
    """A fake engine that yields preset events and optionally creates files."""

    def __init__(self, events=None, side_effect=None):
        self.events = events or [("text", "done")]
        self.side_effect = side_effect
        self.call_count = 0

    def submit(self, prompt: str):
        self.call_count += 1
        if self.side_effect:
            self.side_effect(prompt)
        for event in self.events:
            yield event


def _make_success_side_effect(workspace: Path):
    """Create allowed files so verification passes."""
    def side_effect(prompt):
        src = workspace / "src"
        tests = workspace / "tests"
        src.mkdir(exist_ok=True)
        tests.mkdir(exist_ok=True)
        (src / "__init__.py").write_text("", encoding="utf-8")
        (tests / "__init__.py").write_text("", encoding="utf-8")
        (src / "example.py").write_text("def add(a, b): return a + b\n", encoding="utf-8")
        (tests / "test_example.py").write_text(
            "def test_add(): assert add(1, 2) == 3\n", encoding="utf-8"
        )
    return side_effect


def _mock_subprocess_run(monkeypatch, returncode=0):
    """Mock subprocess.run so verification always returns *returncode*."""
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type(
            "R", (), {"returncode": returncode, "stdout": "", "stderr": ""}
        )(),
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def stores(tmp_path):
    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    step_store = StepArtifactStore(workspace=tmp_path, runtime_store=runtime_store)
    return runtime_store, task_store, step_store


@pytest.fixture
def runner(stores, tmp_path):
    runtime_store, task_store, step_store = stores
    step_executor = StepExecutor(
        workspace=tmp_path,
        runtime_store=runtime_store,
        context_window=32768,
        task_store=task_store,
        step_artifact_store=step_store,
    )
    return DevTaskRunner(
        workspace=tmp_path,
        task_store=task_store,
        step_executor=step_executor,
        step_artifact_store=step_store,
        runtime_store=runtime_store,
        max_steps=10,
    )


def _make_spec(task_id: str = "t1", **overrides) -> TaskSpec:
    defaults = {
        "id": task_id,
        "goal": "Add example module",
        "task_kind": "coding",
        "task_type": "create",
        "executable": True,
        "planning_required": False,
        "allowed_files": ["src/example.py", "tests/test_example.py"],
        "forbidden_files": [],
        "context_budget": 8000,
        "verification": VerificationSpec(
            kind="command",
            command=["python3", "-m", "pytest", "tests/test_example.py", "-q"],
        ),
        "confidence": 0.8,
    }
    defaults.update(overrides)
    return TaskSpec(**defaults)


# ---------------------------------------------------------------------------
# Core runner behaviors
# ---------------------------------------------------------------------------

def test_single_ready_task_runs_to_completion(monkeypatch, runner, stores, tmp_path):
    _mock_subprocess_run(monkeypatch)
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1"))

    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    result = runner.run_ready_tasks(engine)

    assert result.status == "completed"
    assert result.executed_task_ids == ["t1"]
    assert result.terminal_task_id is None
    assert engine.call_count == 1


def test_single_task_failure_stops_run(runner, stores, tmp_path):
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1"))

    # No files created -> verification fails.
    engine = FakeEngine()
    result = runner.run_ready_tasks(engine)

    assert result.status == "failed"
    assert result.terminal_task_id == "t1"
    assert result.terminal_status == "failed"
    assert "verification" in result.next_action.lower() or "fail" in result.next_action.lower()


def test_blocked_task_stops_run(runner, stores, tmp_path):
    _, task_store, _ = stores
    # Low confidence triggers StepExecutor validation block.
    task_store.save_task_spec(_make_spec("t1", confidence=0.5))

    engine = FakeEngine()
    result = runner.run_ready_tasks(engine)

    assert result.status == "blocked"
    assert result.terminal_task_id == "t1"
    assert result.terminal_status == "blocked"
    assert engine.call_count == 0


def test_split_task_stops_run(runner, stores, monkeypatch):
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1"))

    class SplitExecutor:
        def execute_task(self, task_spec, engine, plan_graph=None):
            return TaskResult(task_id=task_spec.id, status="split", next_action="Split task")

    runner.step_executor = SplitExecutor()
    result = runner.run_ready_tasks(FakeEngine())

    assert result.status == "split"
    assert result.terminal_task_id == "t1"
    assert result.terminal_status == "split"


def test_needs_planning_task_stops_run(runner, stores, monkeypatch):
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1"))

    class NeedsPlanningExecutor:
        def execute_task(self, task_spec, engine, plan_graph=None):
            return TaskResult(
                task_id=task_spec.id,
                status="needs_planning",
                next_action="Refine plan",
            )

    runner.step_executor = NeedsPlanningExecutor()
    result = runner.run_ready_tasks(FakeEngine())

    assert result.status == "needs_planning"
    assert result.terminal_task_id == "t1"
    assert result.terminal_status == "needs_planning"


def test_no_ready_tasks_returns_no_ready_or_needs_planning(runner, stores):
    _, task_store, _ = stores
    task_store.save_task_spec(
        _make_spec("t1", executable=False, planning_required=True)
    )

    result = runner.run_ready_tasks(FakeEngine())

    assert result.status in {"no_ready_tasks", "needs_planning"}
    assert result.executed_task_ids == []


def test_max_steps_stops_run(monkeypatch, runner, stores, tmp_path):
    _mock_subprocess_run(monkeypatch)
    _, task_store, _ = stores
    for i in range(5):
        task_store.save_task_spec(_make_spec(f"t{i}"))

    runner.max_steps = 2
    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    result = runner.run_ready_tasks(engine)

    assert result.status == "max_steps_reached"
    assert len(result.executed_task_ids) == 2
    assert engine.call_count == 2


def test_run_summary_written(monkeypatch, runner, stores, tmp_path):
    _mock_subprocess_run(monkeypatch)
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1"))

    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    result = runner.run_ready_tasks(engine)

    summary_path = Path(result.run_summary_path)
    assert summary_path.exists()
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["run_id"] == "test-run"
    assert data["status"] == "completed"
    assert data["executed_task_ids"] == ["t1"]
    assert "task_results_summary" in data
    assert data["next_action"]


def test_executed_task_ids_order_is_stable(monkeypatch, runner, stores, tmp_path):
    _mock_subprocess_run(monkeypatch)
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t-z"))
    task_store.save_task_spec(_make_spec("t-a"))
    task_store.save_task_spec(_make_spec("t-m"))

    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    result = runner.run_ready_tasks(engine)

    assert result.status == "completed"
    assert result.executed_task_ids == ["t-a", "t-m", "t-z"]


def test_does_not_rerun_terminal_result(runner, stores, tmp_path):
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1"))
    task_store.save_task_result(TaskResult(task_id="t1", status="passed"))

    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    result = runner.run_ready_tasks(engine)

    assert result.status == "completed"
    assert result.executed_task_ids == []
    assert engine.call_count == 0


# ---------------------------------------------------------------------------
# DevRunResult serialization
# ---------------------------------------------------------------------------

def test_dev_run_result_round_trip():
    result = DevRunResult(
        run_id="r1",
        status="completed",
        executed_task_ids=["t1"],
        task_results=[TaskResult(task_id="t1", status="passed")],
        next_action="Done",
    )
    restored = DevRunResult.from_json(result.to_json())
    assert restored.run_id == "r1"
    assert restored.status == "completed"
    assert restored.executed_task_ids == ["t1"]
    assert restored.task_results[0].status == "passed"
