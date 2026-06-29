from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.dev_contract import TaskSpec, VerificationSpec
from core.dev_planner import StrictDevPlanner
from core.plan_graph import PlanGraph
from core.runtime_state import RuntimeStateStore
from core.task_spec_store import TaskSpecStore


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

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


@pytest.fixture
def planner_no_runtime(tmp_path):
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=None)
    return StrictDevPlanner(
        workspace=tmp_path,
        task_store=task_store,
        runtime_store=None,
        context_window=32768,
    )


class FakePlannerEngine:
    """Fake planner engine that returns a preset JSON response."""

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


# ---------------------------------------------------------------------------
# build_planning_prompt tests
# ---------------------------------------------------------------------------

def test_build_planning_prompt_contains_json_only_requirement(planner):
    prompt = planner.build_planning_prompt("Build something")
    assert "ONLY a JSON array" in prompt or "ONLY raw JSON" in prompt
    assert "No markdown explanations" in prompt


def test_build_planning_prompt_prohibits_code_and_file_modification(planner):
    prompt = planner.build_planning_prompt("Build something")
    assert "must NOT write code" in prompt
    assert "must NOT modify files" in prompt
    assert "must NOT run commands" in prompt
    assert "must NOT submit commits" in prompt


# ---------------------------------------------------------------------------
# parse_candidate_task_specs tests
# ---------------------------------------------------------------------------

def test_parse_raw_json_success(planner):
    candidates = [_valid_candidate("t1")]
    text = json.dumps(candidates)
    parsed, errors = planner.parse_candidate_task_specs(text)
    assert not errors
    assert len(parsed) == 1
    assert parsed[0]["id"] == "t1"


def test_parse_fenced_json_success(planner):
    candidates = [_valid_candidate("t2")]
    text = "```json\n" + json.dumps(candidates) + "\n```"
    parsed, errors = planner.parse_candidate_task_specs(text)
    assert not errors
    assert len(parsed) == 1
    assert parsed[0]["id"] == "t2"


def test_parse_invalid_json_returns_error_no_exception(planner):
    text = "this is not json { bad"
    parsed, errors = planner.parse_candidate_task_specs(text)
    assert parsed == []
    assert errors
    assert any("json" in e.lower() for e in errors)


def test_parse_tasks_wrapper_success(planner):
    candidates = [_valid_candidate("t3")]
    text = json.dumps({"tasks": candidates})
    parsed, errors = planner.parse_candidate_task_specs(text)
    assert not errors
    assert len(parsed) == 1
    assert parsed[0]["id"] == "t3"


# ---------------------------------------------------------------------------
# plan_goal integration tests
# ---------------------------------------------------------------------------

def test_plan_goal_with_fake_planner_saves_task_spec(planner, tmp_path):
    candidates = [_valid_candidate("task-001")]
    engine = FakePlannerEngine(json.dumps(candidates))
    result = planner.plan_goal("Build example module", engine)

    assert result.status == "planned"
    assert "task-001" in result.valid_task_ids
    loaded = planner.task_store.load_task_spec("task-001")
    assert loaded is not None
    assert loaded.id == "task-001"
    assert loaded.goal == "Add example module"


def test_plan_goal_writes_planning_artifacts(planner, tmp_path):
    candidates = [_valid_candidate("task-002")]
    engine = FakePlannerEngine(json.dumps(candidates))
    result = planner.plan_goal("Build something", engine)

    assert result.planning_prompt_path
    assert result.raw_response_path
    assert result.candidate_artifact_path
    assert result.validation_artifact_path

    base = planner._runtime_base_dir()
    assert (base / "artifacts" / "planning-prompt.md").exists()
    assert (base / "artifacts" / "planner-candidates.json").exists()
    assert (base / "artifacts" / "planner-validation.json").exists()
    assert (base / "artifacts" / "planner-result.json").exists()


def test_planner_engine_called_only_once(planner):
    candidates = [_valid_candidate("task-003")]
    engine = FakePlannerEngine(json.dumps(candidates))
    planner.plan_goal("Build something", engine)
    assert engine.call_count == 1


def test_planner_does_not_call_dev_task_runner(planner, tmp_path, monkeypatch):
    from core import dev_task_runner

    called = False

    def fake_init(*a, **k):
        nonlocal called
        called = True

    monkeypatch.setattr(dev_task_runner.DevTaskRunner, "__init__", fake_init)

    candidates = [_valid_candidate("task-004")]
    engine = FakePlannerEngine(json.dumps(candidates))
    planner.plan_goal("Build something", engine)
    assert not called


def test_planner_does_not_call_step_executor(planner, tmp_path, monkeypatch):
    from core import step_executor

    called = False

    def fake_init(*a, **k):
        nonlocal called
        called = True

    monkeypatch.setattr(step_executor.StepExecutor, "__init__", fake_init)

    candidates = [_valid_candidate("task-005")]
    engine = FakePlannerEngine(json.dumps(candidates))
    planner.plan_goal("Build something", engine)
    assert not called


def test_plan_goal_with_no_candidates_status_needs_planning(planner):
    engine = FakePlannerEngine("[]")
    result = planner.plan_goal("Build something", engine)
    assert result.status == "needs_planning"
    assert result.candidate_count == 0


def test_plan_goal_with_invalid_response_status_invalid_response(planner):
    engine = FakePlannerEngine("not json at all")
    result = planner.plan_goal("Build something", engine)
    assert result.status == "invalid_response"
    assert result.candidate_count == 0
