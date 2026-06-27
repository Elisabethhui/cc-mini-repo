from io import StringIO
from unittest.mock import MagicMock, patch

from rich.console import Console

from core.commands import CommandContext, handle_command
from core.runtime_state import RuntimeStateStore


def test_workflow_resume_without_run_id_lists_available_runs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Seed two runs
    store_a = RuntimeStateStore(str(tmp_path), run_id="run-a")
    store_a.save_state(store_a.default_state())
    store_b = RuntimeStateStore(str(tmp_path), run_id="run-b")
    store_b.save_state(store_b.default_state())

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("workflow-resume", "", ctx)

    output = console.file.getvalue()
    assert "Available workflow runs:" in output
    assert "run-a" in output
    assert "run-b" in output
    assert "Usage: /workflow-resume <run-id>" in output


def test_workflow_resume_shows_blocked_reason(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    store = RuntimeStateStore(str(tmp_path), run_id="blocked-run")
    store.save_state({
        "run_id": "blocked-run",
        "phase": "blocked",
        "goal": "Build feature X",
        "next_action": "Hard stop: context budget exceeded",
        "decisions": [],
        "open_questions": [],
        "artifacts": [],
        "budget_reports": [],
        "current_step": "",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    })

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("workflow-resume", "blocked-run", ctx)

    output = console.file.getvalue()
    assert "blocked" in output.lower()
    assert "Hard stop: context budget exceeded" in output


def test_workflow_resume_shows_done_when_complete(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    store = RuntimeStateStore(str(tmp_path), run_id="done-run")
    store.save_state({
        "run_id": "done-run",
        "phase": "done",
        "goal": "Build feature X",
        "next_action": "Task completed",
        "decisions": [],
        "open_questions": [],
        "artifacts": [],
        "budget_reports": [],
        "current_step": "",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    })

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("workflow-resume", "done-run", ctx)

    output = console.file.getvalue()
    assert "already complete" in output.lower()


def test_workflow_resume_not_found_shows_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("workflow-resume", "nonexistent", ctx)

    output = console.file.getvalue()
    assert "Run not found" in output


def test_workflow_resume_triggers_supervised_execution(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    store = RuntimeStateStore(str(tmp_path), run_id="resume-run")
    store.save_state({
        "run_id": "resume-run",
        "phase": "plan",
        "goal": "Build feature X",
        "next_action": "Plan the implementation",
        "decisions": [],
        "open_questions": [],
        "artifacts": [],
        "budget_reports": [],
        "current_step": "",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    })

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    with patch("core.batch_runner.BatchRunner.resume_supervised") as mock_resume:
        mock_resume.return_value = {"phase": "done", "next_action": "Task completed"}
        handle_command("workflow-resume", "resume-run", ctx)

    output = console.file.getvalue()
    assert "Resuming" in output
    assert "Build feature X" in output
    mock_resume.assert_called_once()
