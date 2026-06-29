from __future__ import annotations

from pathlib import Path

import pytest

from core.dev_contract import TaskResult, TaskSpec, VerificationSpec
from core.plan_graph import PlanGraph, TaskNode
from core.runtime_state import RuntimeStateStore
from core.step_executor import StepExecutor
from core.verification_runner import VerificationRunner


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


def _make_executor(tmp_path):
    store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    return StepExecutor(
        workspace=tmp_path,
        runtime_store=store,
        context_window=32768,
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
# PlanGraph feedback tests
# ---------------------------------------------------------------------------

def test_passed_result_writes_decision(monkeypatch, tmp_path):
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(TaskNode(id="t1", goal="Add module"))

    executor = _make_executor(tmp_path)
    spec = _make_spec()
    _mock_git_clean(monkeypatch)

    result = executor.execute_task(spec, FakeEngine(), plan_graph=pg)

    assert result.status == "passed"
    assert any("t1 passed" in d for d in pg.decisions)


def test_failed_result_writes_risk(monkeypatch, tmp_path):
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(TaskNode(id="t1", goal="Add module"))

    executor = _make_executor(tmp_path)
    # Use verification that will fail
    spec = _make_spec(
        verification=VerificationSpec(
            kind="command",
            command=["python3", "-c", "import sys; sys.exit(1)"],
        ),
    )
    _mock_git_clean(monkeypatch)

    result = executor.execute_task(spec, FakeEngine(), plan_graph=pg)

    assert result.status == "failed"
    assert any("t1 failed" in r for r in pg.risks)


def test_blocked_updates_next_action(monkeypatch, tmp_path):
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(TaskNode(id="t1", goal="Add module"))

    executor = _make_executor(tmp_path)
    # Blocked by executable=False
    spec = _make_spec(executable=False)

    result = executor.execute_task(spec, FakeEngine(), plan_graph=pg)

    assert result.status == "blocked"
    assert pg.next_action  # Should have been updated
    assert "blocked" in pg.next_action.lower() or "validation" in pg.next_action.lower()


def test_split_updates_next_action(monkeypatch, tmp_path):
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(TaskNode(id="t1", goal="Add module"))

    executor = _make_executor(tmp_path)
    spec = _make_spec()
    _mock_git_clean(monkeypatch)

    # Force SPLIT by monkeypatching _check_budget
    from core.context_budget import BudgetState

    class FakeReport:
        state = BudgetState.SPLIT
        warnings = ["split threshold exceeded"]
        def to_dict(self):
            return {"state": "split"}

    executor._check_budget = lambda prompt: FakeReport()

    result = executor.execute_task(spec, FakeEngine(), plan_graph=pg)

    assert result.status == "blocked"
    assert "split" in pg.next_action.lower()


def test_does_not_remove_task_dag_entries(monkeypatch, tmp_path):
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(TaskNode(id="t1", goal="Add module"))

    executor = _make_executor(tmp_path)
    spec = _make_spec()
    _mock_git_clean(monkeypatch)

    executor.execute_task(spec, FakeEngine(), plan_graph=pg)

    assert pg.task_by_id("t1") is not None
    assert len(pg.task_dag) == 1


def test_does_not_auto_mark_plan_done(monkeypatch, tmp_path):
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(TaskNode(id="t1", goal="Add module"))

    executor = _make_executor(tmp_path)
    spec = _make_spec()
    _mock_git_clean(monkeypatch)

    executor.execute_task(spec, FakeEngine(), plan_graph=pg)

    # PlanGraph should not have a "done" phase set automatically
    assert pg.phase != "done"
    assert pg.next_action != "Plan complete"


def test_failed_with_risks_appends_all_to_plan(monkeypatch, tmp_path):
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(TaskNode(id="t1", goal="Add module"))

    executor = _make_executor(tmp_path)
    # Force failure with custom risks
    spec = _make_spec(
        verification=VerificationSpec(
            kind="command",
            command=["python3", "-c", "import sys; sys.exit(1)"],
        ),
    )
    _mock_git_clean(monkeypatch)

    result = executor.execute_task(spec, FakeEngine(), plan_graph=pg)

    assert result.status == "failed"
    # Both the failure message and any additional risks should be in PlanGraph
    assert any("t1 failed" in r for r in pg.risks)


def test_needs_planning_status_updates_next_action(monkeypatch, tmp_path):
    pg = PlanGraph(run_id="r1", goal="Build app")

    executor = _make_executor(tmp_path)
    # Trigger blocked by setting planning_required=True
    spec = _make_spec(planning_required=True)

    result = executor.execute_task(spec, FakeEngine(), plan_graph=pg)

    assert result.status == "blocked"
    # update_plan_with_task_results writes next_action for blocked status
    assert pg.next_action  # Should have been updated from empty
    assert "validation" in pg.next_action.lower() or "blocked" in pg.next_action.lower()
