from __future__ import annotations

from pathlib import Path

import pytest

from core.dev_contract import TaskResult, TaskSpec, VerificationSpec
from core.dev_task_runner import DevTaskRunner
from core.runtime_state import RuntimeStateStore
from core.step_artifact_store import StepArtifactStore
from core.step_executor import StepExecutor
from core.task_spec_store import TaskSpecStore


# ---------------------------------------------------------------------------
# Fake engine helpers
# ---------------------------------------------------------------------------

class FakeEngine:
    """Fake engine that records prompts and optionally mutates the workspace."""

    def __init__(self, side_effect=None):
        self.side_effect = side_effect
        self.call_count = 0
        self.prompts: list[str] = []

    def submit(self, prompt: str):
        self.call_count += 1
        self.prompts.append(prompt)
        if self.side_effect:
            self.side_effect(prompt)
        yield ("text", "done")


def _make_spec(task_id: str = "t1", **overrides) -> TaskSpec:
    defaults = {
        "id": task_id,
        "goal": "Add example module",
        "task_kind": "coding",
        "task_type": "create",
        "executable": True,
        "planning_required": False,
        "allowed_files": ["src/example.py"],
        "forbidden_files": ["src/core/engine.py"],
        "context_budget": 8000,
        "verification": VerificationSpec(
            kind="command",
            command=[
                "python3",
                "-c",
                "import pathlib; t = pathlib.Path('src/example.py').read_text(); assert 'correct' in t, t",
            ],
        ),
        "confidence": 0.8,
    }
    defaults.update(overrides)
    return TaskSpec(**defaults)


def _make_executor(
    tmp_path: Path,
    task_store: TaskSpecStore,
    step_store: StepArtifactStore,
    runtime_store: RuntimeStateStore,
    max_retries: int = 1,
) -> StepExecutor:
    return StepExecutor(
        workspace=tmp_path,
        runtime_store=runtime_store,
        context_window=32768,
        task_store=task_store,
        step_artifact_store=step_store,
        max_retries=max_retries,
    )


def _make_runner(
    tmp_path: Path,
    task_store: TaskSpecStore,
    step_executor: StepExecutor,
    step_store: StepArtifactStore,
    runtime_store: RuntimeStateStore,
    max_retries: int = 1,
) -> DevTaskRunner:
    return DevTaskRunner(
        workspace=tmp_path,
        task_store=task_store,
        step_executor=step_executor,
        step_artifact_store=step_store,
        runtime_store=runtime_store,
        max_steps=10,
        max_retries=max_retries,
    )


@pytest.fixture
def stores(tmp_path):
    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    step_store = StepArtifactStore(workspace=tmp_path, runtime_store=runtime_store)
    return runtime_store, task_store, step_store


def _mock_git_clean(monkeypatch):
    """Make git status fail so changed files come from filesystem fallback."""
    import subprocess

    original = subprocess.run

    def fake_run(*args, **kwargs):
        cmd = args[0] if args else []
        if cmd and cmd[0] == "git":
            return type("R", (), {"returncode": 1, "stdout": "", "stderr": ""})()
        return original(*args, **kwargs)

    monkeypatch.setattr("subprocess.run", fake_run)


# ---------------------------------------------------------------------------
# Retry success / failure
# ---------------------------------------------------------------------------

def test_retry_succeeds_on_second_attempt(monkeypatch, stores, tmp_path):
    _mock_git_clean(monkeypatch)
    runtime_store, task_store, step_store = stores
    task_store.save_task_spec(_make_spec("t1"))

    call_count = [0]

    def side_effect(prompt):
        call_count[0] += 1
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        if call_count[0] == 1:
            (src / "example.py").write_text("wrong content\n", encoding="utf-8")
        else:
            (src / "example.py").write_text("correct content\n", encoding="utf-8")

    engine = FakeEngine(side_effect=side_effect)
    step_executor = _make_executor(tmp_path, task_store, step_store, runtime_store)
    runner = _make_runner(tmp_path, task_store, step_executor, step_store, runtime_store)

    result = runner.run_task("t1", engine)

    assert result.status == "completed"
    assert engine.call_count == 2
    task_result = task_store.load_task_result("t1")
    assert task_result is not None
    assert task_result.status == "passed"
    assert task_result.attempts == 2
    assert task_result.retry_count == 1
    assert task_result.final_test_passed is True


def test_retry_fails_after_two_attempts(monkeypatch, stores, tmp_path):
    _mock_git_clean(monkeypatch)
    runtime_store, task_store, step_store = stores
    task_store.save_task_spec(_make_spec("t1"))

    def side_effect(prompt):
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        (src / "example.py").write_text("wrong content\n", encoding="utf-8")

    engine = FakeEngine(side_effect=side_effect)
    step_executor = _make_executor(tmp_path, task_store, step_store, runtime_store)
    runner = _make_runner(tmp_path, task_store, step_executor, step_store, runtime_store)

    result = runner.run_task("t1", engine)

    assert result.status == "failed"
    assert engine.call_count == 2
    task_result = task_store.load_task_result("t1")
    assert task_result is not None
    assert task_result.status == "failed"
    assert task_result.attempts == 2
    assert task_result.retry_count == 1
    assert task_result.final_test_passed is False
    assert task_result.review_decision == "revise"
    assert task_result.can_finish is False


# ---------------------------------------------------------------------------
# Retry eligibility
# ---------------------------------------------------------------------------

def test_blocked_status_not_retried(monkeypatch, stores, tmp_path):
    _mock_git_clean(monkeypatch)
    runtime_store, task_store, step_store = stores
    # Low confidence blocks before the engine call.
    task_store.save_task_spec(_make_spec("t1", confidence=0.5))

    engine = FakeEngine()
    step_executor = _make_executor(tmp_path, task_store, step_store, runtime_store)
    runner = _make_runner(tmp_path, task_store, step_executor, step_store, runtime_store)

    result = runner.run_task("t1", engine)

    assert result.status == "blocked"
    assert engine.call_count == 0
    task_result = task_store.load_task_result("t1")
    assert task_result.attempts == 1
    assert task_result.retry_count == 0


def test_budget_split_not_retried(monkeypatch, stores, tmp_path):
    runtime_store, task_store, step_store = stores
    task_store.save_task_spec(_make_spec("t1"))

    from core.context_budget import BudgetState

    executor = _make_executor(tmp_path, task_store, step_store, runtime_store)

    class SplitReport:
        state = BudgetState.SPLIT
        warnings = ["usage ratio exceeds split threshold"]

        def to_dict(self):
            return {"state": "split", "warnings": self.warnings}

    executor._check_budget = lambda prompt: SplitReport()

    runner = _make_runner(tmp_path, task_store, executor, step_store, runtime_store)
    engine = FakeEngine()

    result = runner.run_task("t1", engine)

    assert result.status == "blocked"
    assert engine.call_count == 0
    task_result = task_store.load_task_result("t1")
    assert task_result.attempts == 1
    assert task_result.retry_count == 0


def test_needs_planning_not_retried(monkeypatch, stores, tmp_path):
    _mock_git_clean(monkeypatch)
    runtime_store, task_store, step_store = stores
    task_store.save_task_spec(_make_spec("t1", planning_required=True, executable=False))

    engine = FakeEngine()
    step_executor = _make_executor(tmp_path, task_store, step_store, runtime_store)
    runner = _make_runner(tmp_path, task_store, step_executor, step_store, runtime_store)

    result = runner.run_task("t1", engine)

    assert result.status == "needs_planning"
    assert engine.call_count == 0
    # No execution attempt is recorded for tasks blocked before the engine.


def test_forbidden_file_modified_not_retried(monkeypatch, stores, tmp_path):
    runtime_store, task_store, step_store = stores
    task_store.save_task_spec(_make_spec("t1"))

    # Git status claims a forbidden file was modified.
    monkeypatch.setattr(
        "subprocess.run",
        lambda *a, **k: type(
            "R", (), {"returncode": 0, "stdout": " M src/core/engine.py\n", "stderr": ""}
        )(),
    )

    engine = FakeEngine()
    step_executor = _make_executor(tmp_path, task_store, step_store, runtime_store)
    runner = _make_runner(tmp_path, task_store, step_executor, step_store, runtime_store)

    result = runner.run_task("t1", engine)

    assert result.status == "blocked"
    assert engine.call_count == 1
    task_result = task_store.load_task_result("t1")
    assert task_result.attempts == 1
    assert task_result.retry_count == 0
    assert any("Forbidden" in r for r in task_result.risks)


# ---------------------------------------------------------------------------
# Retry bounds
# ---------------------------------------------------------------------------

def test_max_retries_one_only_retries_once(monkeypatch, stores, tmp_path):
    _mock_git_clean(monkeypatch)
    runtime_store, task_store, step_store = stores
    task_store.save_task_spec(_make_spec("t1"))

    def side_effect(prompt):
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        (src / "example.py").write_text("wrong content\n", encoding="utf-8")

    engine = FakeEngine(side_effect=side_effect)
    # Even though we request 2 retries, the runner clamps to 1.
    step_executor = _make_executor(tmp_path, task_store, step_store, runtime_store, max_retries=2)
    runner = _make_runner(tmp_path, task_store, step_executor, step_store, runtime_store, max_retries=2)

    result = runner.run_task("t1", engine)

    assert result.status == "failed"
    assert engine.call_count == 2
    task_result = task_store.load_task_result("t1")
    assert task_result.attempts == 2
    assert task_result.retry_count == 1


def test_no_retry_flag_does_not_retry(monkeypatch, stores, tmp_path):
    _mock_git_clean(monkeypatch)
    runtime_store, task_store, step_store = stores
    task_store.save_task_spec(_make_spec("t1"))

    def side_effect(prompt):
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        (src / "example.py").write_text("wrong content\n", encoding="utf-8")

    engine = FakeEngine(side_effect=side_effect)
    step_executor = _make_executor(tmp_path, task_store, step_store, runtime_store, max_retries=0)
    runner = _make_runner(tmp_path, task_store, step_executor, step_store, runtime_store, max_retries=0)

    result = runner.run_task("t1", engine)

    assert result.status == "failed"
    assert engine.call_count == 1
    task_result = task_store.load_task_result("t1")
    assert task_result.attempts == 1
    assert task_result.retry_count == 0


# ---------------------------------------------------------------------------
# Retry prompt content
# ---------------------------------------------------------------------------

def test_retry_prompt_contains_failure_summary(monkeypatch, stores, tmp_path):
    _mock_git_clean(monkeypatch)
    runtime_store, task_store, step_store = stores
    task_store.save_task_spec(_make_spec("t1"))

    call_count = [0]

    def side_effect(prompt):
        call_count[0] += 1
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        if call_count[0] == 1:
            (src / "example.py").write_text("wrong content\n", encoding="utf-8")
        else:
            (src / "example.py").write_text("correct content\n", encoding="utf-8")

    engine = FakeEngine(side_effect=side_effect)
    step_executor = _make_executor(tmp_path, task_store, step_store, runtime_store)
    runner = _make_runner(tmp_path, task_store, step_executor, step_store, runtime_store)

    runner.run_task("t1", engine)

    assert len(engine.prompts) == 2
    retry_prompt = engine.prompts[1]
    assert "Retry Task Execution" in retry_prompt
    assert "t1" in retry_prompt
    assert "wrong content" in retry_prompt or "stdout summary" in retry_prompt
    assert "Allowed Files" in retry_prompt
    assert "Forbidden Files" in retry_prompt
    assert "Verification Spec" in retry_prompt
    assert "Fix ONLY the failure reason" in retry_prompt
    assert "Do NOT modify any file outside Allowed Files" in retry_prompt
    assert "Do NOT modify any Forbidden Files" in retry_prompt


# ---------------------------------------------------------------------------
# changed_files still from filesystem, not assistant text
# ---------------------------------------------------------------------------

def test_changed_files_not_from_assistant_text_on_retry(monkeypatch, stores, tmp_path):
    _mock_git_clean(monkeypatch)
    runtime_store, task_store, step_store = stores
    task_store.save_task_spec(_make_spec("t1"))

    call_count = [0]

    def side_effect(prompt):
        call_count[0] += 1
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        if call_count[0] == 1:
            (src / "example.py").write_text("wrong content\n", encoding="utf-8")
        else:
            (src / "example.py").write_text("correct content\n", encoding="utf-8")

    # Engine text claims a fake file was changed.
    class TextEngine:
        def __init__(self):
            self.call_count = 0

        def submit(self, prompt: str):
            self.call_count += 1
            side_effect(prompt)
            yield ("text", "I changed src/fake-assistant.py")

    engine = TextEngine()
    step_executor = _make_executor(tmp_path, task_store, step_store, runtime_store)
    runner = _make_runner(tmp_path, task_store, step_executor, step_store, runtime_store)

    result = runner.run_task("t1", engine)

    assert result.status == "completed"
    task_result = task_store.load_task_result("t1")
    assert "src/fake-assistant.py" not in task_result.changed_files
    assert "src/example.py" in task_result.changed_files
