from __future__ import annotations

import pytest

from core.dev_contract import TaskResult, TaskSpec, VerificationSpec


# ---------------------------------------------------------------------------
# Round-trip tests
# ---------------------------------------------------------------------------

def test_verification_spec_json_round_trip():
    v = VerificationSpec(
        kind="command",
        command=["pytest", "tests/"],
        expected_exit_code=0,
        timeout_seconds=60,
        expected_artifacts=[],
        notes="Run all tests",
    )
    restored = VerificationSpec.from_json(v.to_json())
    assert restored.kind == "command"
    assert restored.command == ["pytest", "tests/"]
    assert restored.expected_exit_code == 0
    assert restored.timeout_seconds == 60
    assert restored.notes == "Run all tests"


def test_task_spec_json_round_trip():
    v = VerificationSpec(kind="artifact", expected_artifacts=["out.md"])
    t = TaskSpec(
        id="t1",
        goal="Write docs",
        task_kind="coding",
        task_type="create",
        executable=True,
        allowed_files=["docs/guide.md"],
        context_budget=4000,
        verification=v,
        done_definition=["Docs written"],
        depends_on=["t0"],
        source_plan_id="plan-1",
        run_id="run-1",
        risks=["Might be too long"],
        assumptions=["Python 3.11+"],
        confidence=0.75,
    )
    restored = TaskSpec.from_json(t.to_json())
    assert restored.id == "t1"
    assert restored.goal == "Write docs"
    assert restored.task_kind == "coding"
    assert restored.task_type == "create"
    assert restored.executable is True
    assert restored.allowed_files == ["docs/guide.md"]
    assert restored.context_budget == 4000
    assert restored.verification.kind == "artifact"
    assert restored.verification.expected_artifacts == ["out.md"]
    assert restored.done_definition == ["Docs written"]
    assert restored.depends_on == ["t0"]
    assert restored.source_plan_id == "plan-1"
    assert restored.run_id == "run-1"
    assert restored.risks == ["Might be too long"]
    assert restored.assumptions == ["Python 3.11+"]
    assert restored.confidence == 0.75


def test_task_result_json_round_trip():
    r = TaskResult(
        task_id="t1",
        status="passed",
        changed_files=["a.py"],
        verification_command=["pytest"],
        verification_passed=True,
        artifact_paths=["art.md"],
        next_action="Next",
        risks=["R1"],
        notes="Done",
    )
    restored = TaskResult.from_json(r.to_json())
    assert restored.task_id == "t1"
    assert restored.status == "passed"
    assert restored.changed_files == ["a.py"]
    assert restored.verification_command == ["pytest"]
    assert restored.verification_passed is True
    assert restored.artifact_paths == ["art.md"]
    assert restored.next_action == "Next"
    assert restored.risks == ["R1"]
    assert restored.notes == "Done"


# ---------------------------------------------------------------------------
# Invalid VerificationSpec
# ---------------------------------------------------------------------------

def test_invalid_verification_command_empty():
    v = VerificationSpec(kind="command", command=[])
    errors = v.validate()
    assert any("command" in e.lower() for e in errors)


def test_invalid_verification_artifact_empty():
    v = VerificationSpec(kind="artifact", expected_artifacts=[])
    errors = v.validate()
    assert any("expected_artifacts" in e.lower() for e in errors)


def test_invalid_verification_manual_empty_notes():
    v = VerificationSpec(kind="manual", notes="")
    errors = v.validate()
    assert any("notes" in e.lower() for e in errors)


def test_valid_contract_verification():
    v = VerificationSpec(kind="contract")
    assert v.validate() == []


# ---------------------------------------------------------------------------
# Invalid TaskSpec
# ---------------------------------------------------------------------------

def test_invalid_task_spec_context_budget_zero():
    t = TaskSpec(id="t1", context_budget=0)
    errors = t.validate()
    assert any("context_budget" in e.lower() for e in errors)


def test_invalid_task_spec_confidence_out_of_range():
    t = TaskSpec(id="t1", context_budget=100, confidence=1.5)
    errors = t.validate()
    assert any("confidence" in e.lower() for e in errors)

    t2 = TaskSpec(id="t2", context_budget=100, confidence=-0.1)
    errors2 = t2.validate()
    assert any("confidence" in e.lower() for e in errors2)


def test_invalid_task_spec_planning_required_but_executable():
    t = TaskSpec(
        id="t1",
        context_budget=100,
        planning_required=True,
        executable=True,
    )
    errors = t.validate()
    assert any("planning_required" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Valid TaskSpec edge cases
# ---------------------------------------------------------------------------

def test_valid_executable_coding_with_allowed_files():
    t = TaskSpec(
        id="t1",
        context_budget=100,
        task_kind="coding",
        executable=True,
        allowed_files=["src/a.py"],
        verification=VerificationSpec(kind="command", command=["pytest"]),
    )
    assert t.validate() == []


def test_valid_executable_coding_without_allowed_files_but_risk_notes_boundaries():
    t = TaskSpec(
        id="t1",
        context_budget=100,
        task_kind="coding",
        executable=True,
        allowed_files=[],
        risks=["File boundaries are unknown"],
        verification=VerificationSpec(kind="command", command=["pytest"]),
    )
    assert t.validate() == []


def test_invalid_executable_coding_without_allowed_files_or_boundary_risk():
    t = TaskSpec(
        id="t1",
        context_budget=100,
        task_kind="coding",
        executable=True,
        allowed_files=[],
        risks=[],
        verification=VerificationSpec(kind="command", command=["pytest"]),
    )
    errors = t.validate()
    assert any("allowed_files" in e.lower() for e in errors)
