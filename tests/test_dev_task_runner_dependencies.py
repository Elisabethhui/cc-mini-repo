from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.dev_contract import TaskResult, TaskSpec, VerificationSpec
from core.dev_task_runner import DevTaskRunner
from core.runtime_state import RuntimeStateStore
from core.step_artifact_store import StepArtifactStore
from core.step_executor import StepExecutor
from core.task_spec_store import TaskSpecStore


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class FakeEngine:
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
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type(
            "R", (), {"returncode": returncode, "stdout": "", "stderr": ""}
        )(),
    )


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
# Dependency execution
# ---------------------------------------------------------------------------

def test_a_passed_then_b_executes(monkeypatch, runner, stores, tmp_path):
    _mock_subprocess_run(monkeypatch)
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("A"))
    task_store.save_task_spec(_make_spec("B", depends_on=["A"]))

    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    result = runner.run_ready_tasks(engine)

    assert result.status == "completed"
    assert result.executed_task_ids == ["A", "B"]
    assert engine.call_count == 2


def test_a_failed_then_b_not_executed(runner, stores, tmp_path):
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("A"))
    task_store.save_task_spec(_make_spec("B", depends_on=["A"]))

    # Engine does not create files, so verification fails for A.
    engine = FakeEngine()
    result = runner.run_ready_tasks(engine)

    assert result.status == "failed"
    assert result.executed_task_ids == ["A"]
    assert "B" not in result.executed_task_ids


def test_a_blocked_then_b_not_executed(runner, stores):
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("A", confidence=0.5))
    task_store.save_task_spec(_make_spec("B", depends_on=["A"]))

    engine = FakeEngine()
    result = runner.run_ready_tasks(engine)

    assert result.status == "blocked"
    assert result.executed_task_ids == ["A"]
    assert "B" not in result.executed_task_ids


def test_multiple_ready_tasks_execute_in_task_id_order(monkeypatch, runner, stores, tmp_path):
    _mock_subprocess_run(monkeypatch)
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("z"))
    task_store.save_task_spec(_make_spec("a"))
    task_store.save_task_spec(_make_spec("m"))

    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    result = runner.run_ready_tasks(engine)

    assert result.status == "completed"
    assert result.executed_task_ids == ["a", "m", "z"]


def test_missing_dependency_blocks_task_and_adds_warning(monkeypatch, runner, stores):
    _mock_subprocess_run(monkeypatch)
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("A"))
    task_store.save_task_spec(_make_spec("B", depends_on=["A", "missing"]))

    preview = runner.preview_ready_tasks()
    assert "B" not in preview["ready"]
    pending_b = next(p for p in preview["pending"] if p["task_id"] == "B")
    assert any(d["task_id"] == "missing" for d in pending_b["blocked_by"])

    engine = FakeEngine()
    result = runner.run_ready_tasks(engine)

    # A executes because it is ready; B stays pending.
    assert result.status == "no_ready_tasks"
    assert "A" in result.executed_task_ids
    assert "B" not in result.executed_task_ids
    assert any("missing" in w for w in result.warnings)


def test_run_task_rejects_when_dependencies_not_met(runner, stores):
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("A"))
    task_store.save_task_spec(_make_spec("B", depends_on=["A"]))

    engine = FakeEngine()
    result = runner.run_task("B", engine)

    assert result.status == "blocked"
    assert result.terminal_task_id == "B"
    assert "A" in result.next_action
    assert engine.call_count == 0


def test_run_task_executes_when_dependencies_met(monkeypatch, runner, stores, tmp_path):
    _mock_subprocess_run(monkeypatch)
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("A"))
    task_store.save_task_spec(_make_spec("B", depends_on=["A"]))
    task_store.save_task_result(TaskResult(task_id="A", status="passed"))

    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    result = runner.run_task("B", engine)

    assert result.status == "completed"
    assert result.executed_task_ids == ["B"]
    assert engine.call_count == 1


def test_passed_task_not_rerun_via_run_task(runner, stores, tmp_path):
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("A"))
    task_store.save_task_result(TaskResult(task_id="A", status="passed"))

    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    result = runner.run_task("A", engine)

    assert engine.call_count == 0
    assert result.skipped_task_ids == ["A"]
    assert result.status in {"completed", "passed"}
