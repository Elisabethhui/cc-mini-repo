from __future__ import annotations

import json

import pytest

from core.dev_planner import StrictDevPlanner
from core.plan_graph import PlanGraph, TaskNode
from core.runtime_state import RuntimeStateStore
from core.task_spec_store import TaskSpecStore


@pytest.fixture
def planner(tmp_path):
    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    return StrictDevPlanner(
        workspace=tmp_path,
        task_store=task_store,
        runtime_store=runtime_store,
        context_window=32768,
    )


class FakePlannerEngine:
    def __init__(self, response: str):
        self.response = response
        self.call_count = 0

    def run(self, prompt: str) -> str:
        self.call_count += 1
        return self.response


def _valid_candidate(task_id: str = "task-001") -> dict:
    return {
        "id": task_id,
        "goal": "Add example module",
        "task_kind": "coding",
        "task_type": "create",
        "executable": True,
        "planning_required": False,
        "allowed_files": ["src/example.py", "tests/test_example.py"],
        "forbidden_files": [],
        "context_budget": 8000,
        "max_files_to_read": 5,
        "max_files_to_edit": 3,
        "verification": {
            "kind": "command",
            "command": ["python", "-m", "pytest", "tests/test_example.py", "-q"],
        },
        "done_definition": ["Tests pass"],
        "depends_on": [],
        "confidence": 0.8,
        "risks": [],
        "assumptions": [],
    }


def _invalid_candidate(task_id: str = "task-bad") -> dict:
    return {
        "id": task_id,
        "goal": "Bad task",
        "task_kind": "coding",
        "task_type": "create",
        "executable": True,
        "planning_required": False,
        "allowed_files": [],
        "forbidden_files": [],
        "context_budget": 8000,
        "max_files_to_read": 5,
        "max_files_to_edit": 3,
        "verification": {"kind": "contract"},
        "done_definition": [],
        "depends_on": [],
        "confidence": 0.8,
        "risks": [],
        "assumptions": [],
    }


# ---------------------------------------------------------------------------
# PlanGraph feedback tests
# ---------------------------------------------------------------------------

def test_valid_tasks_written_to_plan_graph_task_dag(planner):
    pg = PlanGraph(run_id="r1", goal="Build app")
    candidates = [_valid_candidate("task-001")]
    engine = FakePlannerEngine(json.dumps(candidates))
    result = planner.plan_goal("Build something", engine, plan_graph=pg)

    assert result.status == "planned"
    node = pg.task_by_id("task-001")
    assert node is not None
    assert node.goal == "Add example module"


def test_no_duplicate_task_ids_in_plan_graph(planner):
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(TaskNode(id="task-001", goal="Existing"))

    candidates = [_valid_candidate("task-001")]
    engine = FakePlannerEngine(json.dumps(candidates))
    result = planner.plan_goal("Build something", engine, plan_graph=pg)

    assert result.status == "planned"
    nodes = [n for n in pg.task_dag if n.id == "task-001"]
    assert len(nodes) == 1
    assert nodes[0].goal == "Existing"


def test_invalid_candidate_reasons_written_to_plan_graph_risks(planner):
    pg = PlanGraph(run_id="r1", goal="Build app")
    candidates = [_invalid_candidate("task-bad")]
    engine = FakePlannerEngine(json.dumps(candidates))
    result = planner.plan_goal("Build something", engine, plan_graph=pg)

    assert result.status == "blocked"
    assert any("contract" in r.lower() for r in pg.risks)


def test_planned_status_next_action_points_to_review_or_run(planner):
    pg = PlanGraph(run_id="r1", goal="Build app")
    candidates = [_valid_candidate("task-001")]
    engine = FakePlannerEngine(json.dumps(candidates))
    result = planner.plan_goal("Build something", engine, plan_graph=pg)

    assert result.status == "planned"
    assert "review" in pg.next_action.lower() or "run" in pg.next_action.lower()


def test_invalid_response_next_action_points_to_refine_goal(planner):
    pg = PlanGraph(run_id="r1", goal="Build app")
    engine = FakePlannerEngine("not json")
    result = planner.plan_goal("Build something", engine, plan_graph=pg)

    assert result.status == "invalid_response"
    assert "refine" in pg.next_action.lower() or "retry" in pg.next_action.lower()


def test_does_not_auto_delete_existing_task_dag(planner):
    pg = PlanGraph(run_id="r1", goal="Build app")
    pg.add_task(TaskNode(id="existing-task", goal="Keep me"))

    candidates = [_valid_candidate("task-new")]
    engine = FakePlannerEngine(json.dumps(candidates))
    planner.plan_goal("Build something", engine, plan_graph=pg)

    assert pg.task_by_id("existing-task") is not None
    assert pg.task_by_id("task-new") is not None


def test_does_not_auto_mark_plan_graph_done(planner):
    pg = PlanGraph(run_id="r1", goal="Build app")
    candidates = [_valid_candidate("task-001")]
    engine = FakePlannerEngine(json.dumps(candidates))
    planner.plan_goal("Build something", engine, plan_graph=pg)

    assert pg.phase != "done"
    assert pg.phase != "completed"
