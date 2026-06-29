from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock, patch

from rich.console import Console

from core.commands import CommandContext, handle_command
from core.dev_contract import TaskResult, TaskSpec, VerificationSpec


def _make_spec(task_id: str = "task-001", **overrides) -> TaskSpec:
    defaults = {
        "id": task_id,
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


def test_dev_dry_run_does_not_call_engine(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    from core.runtime_state import RuntimeStateStore
    from core.task_spec_store import TaskSpecStore

    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    task_store.save_task_spec(_make_spec("task-001"))

    console = Console(file=StringIO())
    engine = MagicMock()
    ctx = CommandContext(
        engine=engine,
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("dev", "--dry-run task-001", ctx)

    output = console.file.getvalue()
    assert "task-001" in output
    assert "Ready to run" in output
    engine.submit.assert_not_called()
    if hasattr(engine, "run"):
        engine.run.assert_not_called()


def test_dev_run_executes_task(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    from core.runtime_state import RuntimeStateStore
    from core.task_spec_store import TaskSpecStore

    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    task_store.save_task_spec(_make_spec("task-001"))

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    mock_result = MagicMock()
    mock_result.status = "completed"
    mock_result.run_id = "test-run"
    mock_result.executed_task_ids = ["task-001"]
    mock_result.terminal_task_id = None
    mock_result.terminal_status = None
    mock_result.run_summary_path = "run-summary.json"
    mock_result.next_action = "Done"
    mock_result.warnings = []
    mock_result.risks = []

    with patch("core.dev_task_runner.DevTaskRunner") as MockRunner:
        mock_instance = MockRunner.return_value
        mock_instance.run_task.return_value = mock_result
        handle_command("dev", "--run task-001", ctx)
        mock_instance.run_task.assert_called_once_with(
            task_id="task-001", engine=ctx.engine
        )

    output = console.file.getvalue()
    assert "completed" in output


def test_dev_run_rejects_planning_required_task(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    from core.runtime_state import RuntimeStateStore
    from core.task_spec_store import TaskSpecStore

    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    task_store.save_task_spec(
        _make_spec("task-001", planning_required=True, executable=False)
    )

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    with patch("core.dev_task_runner.DevTaskRunner") as MockRunner:
        handle_command("dev", "--run task-001", ctx)
        MockRunner.assert_not_called()

    output = console.file.getvalue()
    assert "requires planning" in output.lower()


def test_dev_run_rejects_non_executable_task(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    from core.runtime_state import RuntimeStateStore
    from core.task_spec_store import TaskSpecStore

    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    task_store.save_task_spec(_make_spec("task-001", executable=False))

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    with patch("core.dev_task_runner.DevTaskRunner") as MockRunner:
        handle_command("dev", "--run task-001", ctx)
        MockRunner.assert_not_called()

    output = console.file.getvalue()
    assert "not executable" in output.lower()


def test_dev_run_rejects_unsatisfied_dependency(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    from core.runtime_state import RuntimeStateStore
    from core.task_spec_store import TaskSpecStore

    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    task_store.save_task_spec(_make_spec("task-001"))
    task_store.save_task_spec(_make_spec("task-002", depends_on=["task-001"]))

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    with patch("core.dev_task_runner.DevTaskRunner") as MockRunner:
        handle_command("dev", "--run task-002", ctx)
        MockRunner.assert_not_called()

    output = console.file.getvalue()
    assert "dependency" in output.lower() or "blocked" in output.lower()


def test_dev_run_allows_satisfied_dependency(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    from core.runtime_state import RuntimeStateStore
    from core.task_spec_store import TaskSpecStore

    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    task_store.save_task_spec(_make_spec("task-001"))
    task_store.save_task_spec(_make_spec("task-002", depends_on=["task-001"]))
    task_store.save_task_result(TaskResult(task_id="task-001", status="passed"))

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    mock_result = MagicMock()
    mock_result.status = "completed"
    mock_result.run_id = "test-run"
    mock_result.executed_task_ids = ["task-002"]
    mock_result.terminal_task_id = None
    mock_result.terminal_status = None
    mock_result.run_summary_path = "run-summary.json"
    mock_result.next_action = "Done"
    mock_result.warnings = []
    mock_result.risks = []

    with patch("core.dev_task_runner.DevTaskRunner") as MockRunner:
        mock_instance = MockRunner.return_value
        mock_instance.run_task.return_value = mock_result
        handle_command("dev", "--run task-002", ctx)
        mock_instance.run_task.assert_called_once_with(
            task_id="task-002", engine=ctx.engine
        )

    output = console.file.getvalue()
    assert "completed" in output
