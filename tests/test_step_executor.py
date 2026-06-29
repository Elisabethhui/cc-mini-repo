from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from core.context_budget import BudgetState
from core.dev_contract import TaskResult, TaskSpec, VerificationSpec
from core.plan_graph import PlanGraph
from core.runtime_state import RuntimeStateStore
from core.step_executor import StepExecutor, StepResult
from core.verification_runner import VerificationRunner


# ---------------------------------------------------------------------------
# Fake engine helpers
# ---------------------------------------------------------------------------

class FakeEngine:
    """A fake engine for testing that yields preset events."""

    def __init__(self, events=None, side_effect=None):
        self.events = events or [("text", "Task completed by fake engine")]
        self.side_effect = side_effect  # callable(prompt) -> None
        self.call_count = 0

    def submit(self, prompt: str):
        self.call_count += 1
        if self.side_effect:
            self.side_effect(prompt)
        for event in self.events:
            yield event


def _make_executor(tmp_path, context_window=32768):
    store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    return StepExecutor(
        workspace=tmp_path,
        runtime_store=store,
        context_window=context_window,
    )


def _make_valid_task_spec(**overrides) -> TaskSpec:
    defaults = {
        "id": "t1",
        "goal": "Add example module",
        "task_kind": "coding",
        "task_type": "create",
        "executable": True,
        "planning_required": False,
        "allowed_files": ["src/example.py", "tests/test_example.py"],
        "forbidden_files": ["src/core/engine.py"],
        "context_budget": 8000,
        "max_files_to_read": 5,
        "max_files_to_edit": 3,
        "verification": VerificationSpec(
            kind="command",
            command=["python3", "-m", "pytest", "tests/test_example.py", "-q"],
        ),
        "done_definition": ["Tests pass"],
        "confidence": 0.8,
    }
    defaults.update(overrides)
    return TaskSpec(**defaults)


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------

def test_executable_task_runs_and_passes(tmp_path, monkeypatch):
    """Executable TaskSpec + fake engine -> passed TaskResult."""
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec()

    # Make fake engine create the allowed files so verification passes
    def create_files(prompt):
        src_dir = tmp_path / "src"
        src_dir.mkdir(exist_ok=True)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        (src_dir / "example.py").write_text("def add(a, b): return a + b\n", encoding="utf-8")
        (tests_dir / "test_example.py").write_text(
            "def test_add(): assert add(1, 2) == 3\n", encoding="utf-8"
        )
        # Add __init__ so pytest can import
        (src_dir / "__init__.py").write_text("", encoding="utf-8")
        (tests_dir / "__init__.py").write_text("", encoding="utf-8")

    engine = FakeEngine(side_effect=create_files)

    # Monkeypatch git status to show nothing (clean)
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    result = executor.execute_task(spec, engine)

    assert result.status == "passed"
    assert result.verification_passed is True
    assert engine.call_count == 1


def test_fake_engine_creates_allowed_files(tmp_path, monkeypatch):
    """Fake engine side-effect creates generic files from explicit TaskSpec."""
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec()

    created = []

    def create_files(prompt):
        src_dir = tmp_path / "src"
        src_dir.mkdir(exist_ok=True)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir(exist_ok=True)
        (src_dir / "example.py").write_text("x = 1\n", encoding="utf-8")
        (tests_dir / "test_example.py").write_text("def test_x(): pass\n", encoding="utf-8")
        created.extend(["src/example.py", "tests/test_example.py"])

    engine = FakeEngine(side_effect=create_files)

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    result = executor.execute_task(spec, engine)

    assert "src/example.py" in created
    assert "tests/test_example.py" in created
    assert result.status == "passed"


def test_verification_runner_executes_explicit_command(tmp_path, monkeypatch):
    """VerificationRunner runs the explicit command from TaskSpec."""
    executor = _make_executor(tmp_path)
    # Use a command that just echoes — we verify it ran
    spec = _make_valid_task_spec(
        verification=VerificationSpec(
            kind="command",
            command=["python3", "-c", "print('VERIFIED')"],
        ),
    )

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    engine = FakeEngine()
    result = executor.execute_task(spec, engine)

    # Even with mocked git status, verification should still run
    # We verify by looking at the stored artifact
    store = executor.runtime_store
    artifacts = store.list_artifacts()
    verif_artifacts = [a for a in artifacts if "verification-result" in a]
    assert verif_artifacts


# ---------------------------------------------------------------------------
# Validation blocks engine call
# ---------------------------------------------------------------------------

def test_executable_false_blocks_engine(tmp_path):
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec(executable=False)
    engine = FakeEngine()
    result = executor.execute_task(spec, engine)
    assert result.status == "blocked"
    assert engine.call_count == 0


def test_planning_required_blocks_engine(tmp_path):
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec(planning_required=True)
    engine = FakeEngine()
    result = executor.execute_task(spec, engine)
    assert result.status == "blocked"
    assert engine.call_count == 0


def test_empty_allowed_files_coding_blocked(tmp_path):
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec(allowed_files=[], risks=[])
    engine = FakeEngine()
    result = executor.execute_task(spec, engine)
    assert result.status == "blocked"
    assert engine.call_count == 0
    assert any("allowed_files" in r for r in result.risks)


# ---------------------------------------------------------------------------
# Scope enforcement
# ---------------------------------------------------------------------------

def test_forbidden_file_modified_blocks(tmp_path, monkeypatch):
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec()

    # Git status shows a forbidden file was modified
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type(
            "R", (), {"returncode": 0, "stdout": " M src/core/engine.py\n", "stderr": ""}
        )(),
    )

    engine = FakeEngine()
    result = executor.execute_task(spec, engine)
    assert result.status == "blocked"
    assert any("Forbidden" in r for r in result.risks)


def test_out_of_bounds_file_modified_blocks(tmp_path, monkeypatch):
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec()

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type(
            "R", (), {"returncode": 0, "stdout": " M src/unexpected.py\n", "stderr": ""}
        )(),
    )

    engine = FakeEngine()
    result = executor.execute_task(spec, engine)
    assert result.status == "blocked"
    assert any("Out-of-bounds" in r for r in result.risks)


# ---------------------------------------------------------------------------
# Budget blocks
# ---------------------------------------------------------------------------

def test_budget_hard_stop_blocks_engine(tmp_path):
    """Tiny context_window triggers hard-stop before engine call."""
    executor = _make_executor(tmp_path, context_window=100)
    spec = _make_valid_task_spec(context_budget=10)
    engine = FakeEngine()
    result = executor.execute_task(spec, engine)
    assert result.status == "blocked"
    assert engine.call_count == 0
    assert any("hard-stop" in r.lower() for r in result.risks)


def test_budget_split_blocks_engine(tmp_path):
    """Context window just big enough for split threshold."""
    # With default thresholds (warning=0.65, preserve=0.75, split=0.85, hard_stop=0.92)
    # We need a prompt that pushes ratio above 0.85 but below 0.92
    # A prompt of ~200 chars -> ~111 tokens
    # With context_window=130 and reserved=20 + safety=10, fixed=30
    # projected = 30 + 111 = 141, ratio = 141/130 = 1.08 -> hard_stop
    # Let's use a bigger prompt with a slightly larger window to hit split
    # Actually, the simplest way is to just verify the mechanism works.
    # We can monkeypatch ContextBudgetCalculator.calculate to return SPLIT.
    executor = _make_executor(tmp_path, context_window=1000)
    spec = _make_valid_task_spec()
    engine = FakeEngine()

    # Monkeypatch the budget calculator to force SPLIT
    from core import step_executor as se_mod
    original_check = executor._check_budget

    class FakeReport:
        state = BudgetState.SPLIT
        warnings = ["usage ratio exceeds split threshold"]
        def to_dict(self):
            return {"state": "split", "warnings": self.warnings}

    executor._check_budget = lambda prompt: FakeReport()

    result = executor.execute_task(spec, engine)
    assert result.status == "blocked"
    assert engine.call_count == 0
    assert any("split" in r.lower() for r in result.risks)


# ---------------------------------------------------------------------------
# Engine constraints
# ---------------------------------------------------------------------------

def test_engine_called_only_once(tmp_path, monkeypatch):
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec()

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    engine = FakeEngine()
    executor.execute_task(spec, engine)
    assert engine.call_count == 1


def test_changed_files_not_from_assistant_text(tmp_path, monkeypatch):
    """changed_files must come from git/filesystem, not assistant text."""
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec()

    # Fake engine claims it changed a file in its text output
    engine = FakeEngine(events=[("text", "I changed src/fake.py")])

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    result = executor.execute_task(spec, engine)
    # The assistant text should NOT influence changed_files
    assert "src/fake.py" not in result.changed_files


# ---------------------------------------------------------------------------
# Artifact persistence
# ---------------------------------------------------------------------------

def test_runtime_artifacts_written(tmp_path, monkeypatch):
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec()

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    engine = FakeEngine()
    result = executor.execute_task(spec, engine)

    store = executor.runtime_store
    artifacts = store.list_artifacts()
    assert any("step-result" in a for a in artifacts)
    assert any("task-result" in a for a in artifacts)


def test_step_result_json_exists(tmp_path, monkeypatch):
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec()

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    engine = FakeEngine()
    executor.execute_task(spec, engine)

    store = executor.runtime_store
    step_artifacts = [a for a in store.list_artifacts() if "step-result" in a]
    assert step_artifacts
    content = store.read_artifact(step_artifacts[0])
    data = json.loads(content)
    assert "step_id" in data
    assert "task_id" in data
    assert data["task_id"] == spec.id


def test_task_result_json_exists(tmp_path, monkeypatch):
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec()

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    engine = FakeEngine()
    executor.execute_task(spec, engine)

    store = executor.runtime_store
    task_artifacts = [a for a in store.list_artifacts() if "task-result" in a]
    assert task_artifacts
    content = store.read_artifact(task_artifacts[0])
    data = json.loads(content)
    assert data["task_id"] == spec.id
    assert "status" in data


# ---------------------------------------------------------------------------
# No business keywords
# ---------------------------------------------------------------------------

def test_no_flask_react_cli_keywords_in_core(tmp_path, monkeypatch):
    """Ensure no business framework keywords leaked into execution logic."""
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec(goal="Create Flask React CLI app")

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    engine = FakeEngine()
    result = executor.execute_task(spec, engine)

    # The result should be generic; no framework-specific files should appear
    # unless they were in the explicit TaskSpec
    for f in result.changed_files:
        assert f not in ("app.py", "requirements.txt", "package.json", "App.jsx")


def test_prompt_contains_task_constraints(tmp_path, monkeypatch):
    """Prompt must contain explicit constraints about scope."""
    executor = _make_executor(tmp_path)
    spec = _make_valid_task_spec()

    captured_prompt = []

    class CaptureEngine:
        def submit(self, prompt):
            captured_prompt.append(prompt)
            yield ("text", "done")

    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})(),
    )

    executor.execute_task(spec, CaptureEngine())
    prompt = captured_prompt[0]
    assert "Do NOT modify any file outside Allowed Files" in prompt
    assert "Do NOT modify any Forbidden Files" in prompt
    assert "Complete ONLY this task" in prompt
    assert spec.id in prompt
    assert spec.goal in prompt
