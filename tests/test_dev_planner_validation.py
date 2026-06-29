from __future__ import annotations

import pytest

from core.dev_contract import VerificationSpec
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


def _make_candidate(**overrides) -> dict:
    defaults = {
        "id": "task-001",
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
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# Verification rules
# ---------------------------------------------------------------------------

def test_missing_verification_executable_coding_rejected(planner):
    candidate = _make_candidate(verification={"kind": "contract"})
    result = planner.validate_candidate_task_specs([candidate])
    assert not result.valid_tasks
    assert any("contract" in e.lower() for e in result.errors)


def test_empty_allowed_files_executable_coding_rejected(planner):
    candidate = _make_candidate(allowed_files=[])
    result = planner.validate_candidate_task_specs([candidate])
    assert not result.valid_tasks
    assert any("allowed_files" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# Executable / planning_required combo
# ---------------------------------------------------------------------------

def test_planning_required_true_and_executable_true_rejected(planner):
    candidate = _make_candidate(planning_required=True, executable=True)
    result = planner.validate_candidate_task_specs([candidate])
    assert not result.valid_tasks
    assert any("planning_required" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# Path safety
# ---------------------------------------------------------------------------

def test_absolute_path_rejected(planner):
    candidate = _make_candidate(allowed_files=["/etc/passwd"])
    result = planner.validate_candidate_task_specs([candidate])
    assert not result.valid_tasks
    assert any("unsafe" in e.lower() for e in result.errors)


def test_path_traversal_rejected(planner):
    candidate = _make_candidate(allowed_files=["../secret.py"])
    result = planner.validate_candidate_task_specs([candidate])
    assert not result.valid_tasks
    assert any("unsafe" in e.lower() for e in result.errors)


@pytest.mark.parametrize(
    "bad_path",
    [
        ".env",
        ".git/config",
        "secrets/key.txt",
        "config/token.json",
        "my_password_file.txt",
        "credentials.yaml",
    ],
)
def test_sensitive_path_rejected(planner, bad_path):
    candidate = _make_candidate(allowed_files=[bad_path])
    result = planner.validate_candidate_task_specs([candidate])
    assert not result.valid_tasks
    assert any("sensitive" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# Confidence
# ---------------------------------------------------------------------------

def test_low_confidence_executable_requires_user_review(planner):
    candidate = _make_candidate(confidence=0.5)
    result = planner.validate_candidate_task_specs([candidate])
    assert result.requires_user_review is True
    assert len(result.valid_tasks) == 1
    assert result.valid_tasks[0].executable is False
    assert result.valid_tasks[0].planning_required is True


# ---------------------------------------------------------------------------
# Context budget
# ---------------------------------------------------------------------------

def test_context_budget_zero_rejected(planner):
    candidate = _make_candidate(context_budget=0)
    result = planner.validate_candidate_task_specs([candidate])
    assert not result.valid_tasks
    assert any("context_budget" in e.lower() for e in result.errors)


def test_context_budget_negative_rejected(planner):
    candidate = _make_candidate(context_budget=-100)
    result = planner.validate_candidate_task_specs([candidate])
    assert not result.valid_tasks
    assert any("context_budget" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# Confidence range
# ---------------------------------------------------------------------------

def test_confidence_out_of_range_rejected(planner):
    candidate = _make_candidate(confidence=1.5)
    result = planner.validate_candidate_task_specs([candidate])
    assert not result.valid_tasks
    assert any("confidence" in e.lower() for e in result.errors)

    candidate2 = _make_candidate(confidence=-0.1)
    result2 = planner.validate_candidate_task_specs([candidate2])
    assert not result.valid_tasks
    assert any("confidence" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# depends_on
# ---------------------------------------------------------------------------

def test_invalid_depends_on_produces_warning_or_error(planner):
    candidate = _make_candidate(depends_on=["nonexistent-task"])
    result = planner.validate_candidate_task_specs([candidate])
    # Unknown depends_on is a warning, not an error
    assert len(result.valid_tasks) == 1
    assert any("nonexistent-task" in w.lower() for w in result.warnings)


def test_unsafe_depends_on_produces_error(planner):
    candidate = _make_candidate(depends_on=["../bad"])
    result = planner.validate_candidate_task_specs([candidate])
    assert not result.valid_tasks
    assert any("unsafe" in e.lower() for e in result.errors)


# ---------------------------------------------------------------------------
# Planning task rules
# ---------------------------------------------------------------------------

def test_planning_task_executable_false_with_contract_verification_passes(planner):
    candidate = _make_candidate(
        task_kind="planning",
        task_type="plan",
        executable=False,
        planning_required=True,
        allowed_files=[],
        verification={"kind": "contract"},
        done_definition=[],
    )
    result = planner.validate_candidate_task_specs([candidate])
    assert len(result.valid_tasks) == 1
    assert result.valid_tasks[0].task_kind == "planning"
    assert result.valid_tasks[0].verification.kind == "contract"


# ---------------------------------------------------------------------------
# task_kind / task_type invalid values
# ---------------------------------------------------------------------------

def test_invalid_task_kind_rejected(planner):
    candidate = _make_candidate(task_kind="deploy")
    result = planner.validate_candidate_task_specs([candidate])
    assert not result.valid_tasks
    assert any("task_kind" in e.lower() for e in result.errors)


def test_invalid_task_type_rejected(planner):
    candidate = _make_candidate(task_type="deploy")
    result = planner.validate_candidate_task_specs([candidate])
    assert not result.valid_tasks
    assert any("task_type" in e.lower() for e in result.errors)
