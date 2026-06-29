from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from core.dev_contract import TaskResult, TaskSpec, VerificationSpec
from core.dev_task_runner import DevTaskRunner
from core.plan_graph import PlanGraph, TaskNode
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
def plan_graph():
    pg = PlanGraph(run_id="test-run", goal="Build example module")
    pg.add_task(TaskNode(id="t1", goal="Add example module"))
    return pg


@pytest.fixture
def stores(tmp_path):
    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    step_store = StepArtifactStore(workspace=tmp_path, runtime_store=runtime_store)
    return runtime_store, task_store, step_store


@pytest.fixture
def runner(stores, tmp_path, plan_graph):
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
        plan_graph=plan_graph,
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
# PlanGraph feedback
# ---------------------------------------------------------------------------

def test_passed_task_writes_decision(monkeypatch, runner, stores, plan_graph, tmp_path):
    _mock_subprocess_run(monkeypatch)
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1"))

    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    runner.run_ready_tasks(engine)

    assert any("t1 passed" in d for d in plan_graph.decisions)
    assert len(plan_graph.task_dag) == 1


def test_failed_task_writes_risk(runner, stores, plan_graph):
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1"))

    # No files created -> verification fails.
    engine = FakeEngine()
    runner.run_ready_tasks(engine)

    assert any("t1 failed" in r for r in plan_graph.risks)
    assert len(plan_graph.task_dag) == 1


def test_blocked_task_updates_next_action(runner, stores, plan_graph):
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1", confidence=0.5))

    engine = FakeEngine()
    runner.run_ready_tasks(engine)

    assert plan_graph.next_action
    assert "t1" in plan_graph.next_action or "validation" in plan_graph.next_action.lower()


def test_split_task_updates_next_action(runner, stores, plan_graph):
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1"))

    class SplitExecutor:
        def execute_task(self, task_spec, engine, plan_graph=None):
            return TaskResult(task_id=task_spec.id, status="split", next_action="Slice task")

    runner.step_executor = SplitExecutor()
    runner.run_ready_tasks(FakeEngine())

    assert "Slice task" in plan_graph.next_action


def test_needs_planning_task_updates_next_action(runner, stores, plan_graph):
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1"))

    class NeedsPlanningExecutor:
        def execute_task(self, task_spec, engine, plan_graph=None):
            return TaskResult(
                task_id=task_spec.id,
                status="needs_planning",
                next_action="Refine task",
            )

    runner.step_executor = NeedsPlanningExecutor()
    runner.run_ready_tasks(FakeEngine())

    assert "Refine task" in plan_graph.next_action


def test_completed_run_does_not_delete_task_dag(monkeypatch, runner, stores, plan_graph, tmp_path):
    _mock_subprocess_run(monkeypatch)
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1"))

    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    runner.run_ready_tasks(engine)

    assert len(plan_graph.task_dag) == 1
    assert plan_graph.task_by_id("t1") is not None


def test_max_steps_reached_writes_risk_or_next_action(monkeypatch, runner, stores, plan_graph, tmp_path):
    _mock_subprocess_run(monkeypatch)
    _, task_store, _ = stores
    for i in range(5):
        task_store.save_task_spec(_make_spec(f"t{i}"))

    runner.max_steps = 2
    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    runner.run_ready_tasks(engine)

    assert any("max_steps" in r.lower() or "2" in r for r in plan_graph.risks) or plan_graph.next_action


def test_completed_run_does_not_pretend_done(monkeypatch, runner, stores, plan_graph, tmp_path):
    _mock_subprocess_run(monkeypatch)
    _, task_store, _ = stores
    task_store.save_task_spec(_make_spec("t1"))

    engine = FakeEngine(side_effect=_make_success_side_effect(tmp_path))
    runner.run_ready_tasks(engine)

    # phase should not be hard-coded to a final "archived" state and task_dag
    # must still exist.
    assert plan_graph.phase == "intake"
    assert len(plan_graph.task_dag) == 1
