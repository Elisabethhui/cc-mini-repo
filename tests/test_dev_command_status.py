from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock

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


def test_dev_status_shows_task_states(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    from core.runtime_state import RuntimeStateStore
    from core.task_spec_store import TaskSpecStore

    runtime_store = RuntimeStateStore(str(tmp_path), run_id="test-run")
    task_store = TaskSpecStore(workspace=tmp_path, runtime_store=runtime_store)
    task_store.save_task_spec(_make_spec("task-a"))
    task_store.save_task_spec(_make_spec("task-b", executable=False))
    task_store.save_task_spec(_make_spec("task-c"))
    task_store.save_task_result(TaskResult(task_id="task-c", status="passed"))

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("dev", "--status", ctx)

    output = console.file.getvalue()
    assert "task-a" in output
    assert "task-b" in output
    assert "task-c" in output
    assert "pending" in output
    assert "passed" in output


def test_dev_status_empty_store(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("dev", "--status", ctx)

    output = console.file.getvalue()
    assert "No runs found" in output or "No tasks" in output
