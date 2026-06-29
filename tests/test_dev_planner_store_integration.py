from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.dev_planner import StrictDevPlanner
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
# Store integration tests
# ---------------------------------------------------------------------------

def test_valid_tasks_saved_to_task_spec_store(planner, tmp_path):
    candidates = [_valid_candidate("task-001")]
    engine = FakePlannerEngine(json.dumps(candidates))
    result = planner.plan_goal("Build something", engine)

    assert "task-001" in result.valid_task_ids
    loaded = planner.task_store.load_task_spec("task-001")
    assert loaded is not None
    assert loaded.id == "task-001"


def test_invalid_candidates_do_not_enter_task_spec_store(planner, tmp_path):
    candidates = [_invalid_candidate("task-bad")]
    engine = FakePlannerEngine(json.dumps(candidates))
    result = planner.plan_goal("Build something", engine)

    assert result.valid_task_ids == []
    loaded = planner.task_store.load_task_spec("task-bad")
    assert loaded is None


def test_saved_task_can_be_loaded_back(planner, tmp_path):
    candidates = [_valid_candidate("task-002")]
    engine = FakePlannerEngine(json.dumps(candidates))
    planner.plan_goal("Build something", engine)

    loaded = planner.task_store.load_task_spec("task-002")
    assert loaded is not None
    assert loaded.goal == "Add example module"
    assert loaded.task_kind == "coding"
    assert loaded.executable is True


def test_task_index_json_updated(planner, tmp_path):
    candidates = [_valid_candidate("task-003")]
    engine = FakePlannerEngine(json.dumps(candidates))
    planner.plan_goal("Build something", engine)

    index_path = planner.task_store.base_dir / "task-index.json"
    assert index_path.exists()
    data = json.loads(index_path.read_text(encoding="utf-8"))
    ids = [e["task_id"] for e in data["tasks"]]
    assert "task-003" in ids


def test_planner_result_valid_task_ids_correct(planner, tmp_path):
    candidates = [_valid_candidate("task-004")]
    engine = FakePlannerEngine(json.dumps(candidates))
    result = planner.plan_goal("Build something", engine)

    assert result.valid_task_ids == ["task-004"]


def test_planner_result_saved_task_paths_safe(planner, tmp_path):
    candidates = [_valid_candidate("task-005")]
    engine = FakePlannerEngine(json.dumps(candidates))
    result = planner.plan_goal("Build something", engine)

    assert result.saved_task_paths
    for p in result.saved_task_paths:
        path = Path(p)
        assert not path.is_absolute() or str(path).startswith(str(planner.task_store.base_dir))
        assert ".." not in str(path)


def test_no_candidates_status_needs_planning(planner, tmp_path):
    engine = FakePlannerEngine("[]")
    result = planner.plan_goal("Build something", engine)
    assert result.status == "needs_planning"
    assert result.candidate_count == 0


def test_invalid_response_status_invalid_response(planner, tmp_path):
    engine = FakePlannerEngine("not json")
    result = planner.plan_goal("Build something", engine)
    assert result.status == "invalid_response"
    assert result.candidate_count == 0


def test_low_confidence_task_not_marked_directly_executable(planner, tmp_path):
    cand = _valid_candidate("task-low")
    cand["confidence"] = 0.5
    engine = FakePlannerEngine(json.dumps([cand]))
    result = planner.plan_goal("Build something", engine)

    assert result.status == "requires_review"
    loaded = planner.task_store.load_task_spec("task-low")
    assert loaded is not None
    assert loaded.executable is False
    assert loaded.planning_required is True
