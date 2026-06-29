from __future__ import annotations

from pathlib import Path

import pytest

from core.dev_contract import TaskSpec, VerificationSpec
from core.dev_review import (
    apply_review_to_task_result,
    render_dev_worklog,
    review_task_result,
    write_dev_worklog,
)
from core.dev_task_runner import DevTaskRunner
from core.runtime_state import RuntimeStateStore
from core.step_artifact_store import StepArtifactStore
from core.step_executor import StepExecutor
from core.task_spec_store import TaskSpecStore


class FakeEngine:
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


@pytest.fixture
def stores(tmp_path):
    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    step_store = StepArtifactStore(workspace=tmp_path, runtime_store=runtime_store)
    return runtime_store, task_store, step_store


def _mock_git_clean(monkeypatch):
    import subprocess

    original = subprocess.run

    def fake_run(*args, **kwargs):
        cmd = args[0] if args else []
        if cmd and cmd[0] == "git":
            return type("R", (), {"returncode": 1, "stdout": "", "stderr": ""})()
        return original(*args, **kwargs)

    monkeypatch.setattr("subprocess.run", fake_run)


def _make_runner(tmp_path, task_store, step_store, runtime_store, max_retries=1):
    step_executor = StepExecutor(
        workspace=tmp_path,
        runtime_store=runtime_store,
        context_window=32768,
        task_store=task_store,
        step_artifact_store=step_store,
        max_retries=max_retries,
    )
    return DevTaskRunner(
        workspace=tmp_path,
        task_store=task_store,
        step_executor=step_executor,
        step_artifact_store=step_store,
        runtime_store=runtime_store,
        max_steps=10,
        max_retries=max_retries,
    )


def test_worklog_written_after_passed_task(monkeypatch, stores, tmp_path):
    _mock_git_clean(monkeypatch)
    runtime_store, task_store, step_store = stores
    task_store.save_task_spec(_make_spec("t1"))

    def side_effect(prompt):
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        (src / "example.py").write_text("correct content\n", encoding="utf-8")

    runner = _make_runner(tmp_path, task_store, step_store, runtime_store)
    result = runner.run_task("t1", FakeEngine(side_effect=side_effect))

    worklog_path = Path(result.worklog_path)
    assert worklog_path.exists()
    assert worklog_path == tmp_path / ".ai-dev" / "worklogs" / "test-run.md"


def test_worklog_written_after_failed_task(monkeypatch, stores, tmp_path):
    _mock_git_clean(monkeypatch)
    runtime_store, task_store, step_store = stores
    task_store.save_task_spec(_make_spec("t1"))

    def side_effect(prompt):
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        (src / "example.py").write_text("wrong content\n", encoding="utf-8")

    runner = _make_runner(tmp_path, task_store, step_store, runtime_store)
    result = runner.run_task("t1", FakeEngine(side_effect=side_effect))

    worklog_path = Path(result.worklog_path)
    assert worklog_path.exists()
    text = worklog_path.read_text(encoding="utf-8")
    assert "Dev Worklog: t1" in text


def test_worklog_contains_required_fields(monkeypatch, stores, tmp_path):
    _mock_git_clean(monkeypatch)
    runtime_store, task_store, step_store = stores
    task_store.save_task_spec(_make_spec("t1"))

    def side_effect(prompt):
        src = tmp_path / "src"
        src.mkdir(exist_ok=True)
        (src / "example.py").write_text("correct content\n", encoding="utf-8")

    runner = _make_runner(tmp_path, task_store, step_store, runtime_store)
    result = runner.run_task("t1", FakeEngine(side_effect=side_effect))

    worklog_path = Path(result.worklog_path)
    text = worklog_path.read_text(encoding="utf-8")

    assert "# Dev Worklog: t1" in text
    assert "test-run" in text
    assert "src/example.py" in text
    assert "python3" in text
    assert "attempts:" in text
    assert "retry_count:" in text
    assert "final_test_passed:" in text
    assert "status:" in text
    assert "decision:" in text
    assert "can_finish:" in text
    assert "requires_user_commit:" in text
    assert "Next Action" in text


def test_render_dev_worklog_contains_key_fields():
    from core.dev_contract import TaskResult

    task_result = TaskResult(
        task_id="t1",
        status="passed",
        changed_files=["src/example.py"],
        verification_command=["python3", "-m", "pytest"],
        verification_passed=True,
        attempts=2,
        retry_count=1,
        final_test_passed=True,
        risks=["low risk"],
        next_action="Task t1 complete",
        notes="Add example module",
    )
    review = review_task_result(task_result)
    text = render_dev_worklog(run_id="run-123", task_result=task_result, review_result=review)

    assert "# Dev Worklog: t1" in text
    assert "run-123" in text
    assert "src/example.py" in text
    assert "python3" in text and "pytest" in text
    assert "attempts: 2" in text
    assert "retry_count: 1" in text
    assert "final_test_passed: True" in text
    assert "status: passed" in text
    assert "decision: pass" in text
    assert "can_finish: True" in text
    assert "requires_user_commit: True" in text
    assert "low risk" in text


def test_write_dev_worklog_escapes_directory(tmp_path):
    runtime_store = RuntimeStateStore(str(tmp_path), run_id="../../escape")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    task_store.save_task_spec(_make_spec("t1"))
    spec = task_store.load_task_spec("t1")

    from core.dev_contract import TaskResult

    task_result = TaskResult(task_id="t1", status="passed", verification_passed=True)
    review = review_task_result(task_result)
    path = write_dev_worklog(tmp_path, runtime_store.run_id, task_result, review)

    # Sanitized run_id keeps the file under .ai-dev/worklogs.
    assert path.exists()
    assert path.parent == (tmp_path / ".ai-dev" / "worklogs").resolve()
    assert ".." not in str(path.relative_to(tmp_path))


def test_apply_review_updates_task_result(tmp_path):
    from core.dev_contract import TaskResult

    task_result = TaskResult(
        task_id="t1",
        status="passed",
        verification_passed=True,
    )
    review = review_task_result(task_result)
    worklog_path = tmp_path / ".ai-dev" / "worklogs" / "t1.md"
    worklog_path.parent.mkdir(parents=True, exist_ok=True)
    worklog_path.write_text("log", encoding="utf-8")

    apply_review_to_task_result(task_result, review, worklog_path)

    assert task_result.review_decision == "pass"
    assert task_result.can_finish is True
    assert task_result.requires_user_commit is True
    assert task_result.worklog_path == str(worklog_path)
