from __future__ import annotations

from io import StringIO
from unittest.mock import MagicMock, patch

from rich.console import Console

from core.commands import CommandContext, handle_command


def test_dev_no_args_shows_usage():
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("dev", "", ctx)
    output = console.file.getvalue()
    assert "/dev" in output
    assert "--plan" in output
    assert "--dry-run" in output
    assert "--run" in output
    assert "--status" in output


def test_dev_goal_calls_planner_not_runner(monkeypatch):
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    mock_result = MagicMock()
    mock_result.status = "planned"
    mock_result.run_id = "run-1"
    mock_result.candidate_count = 1
    mock_result.valid_task_ids = ["task-001"]
    mock_result.invalid_candidate_count = 0
    mock_result.next_action = "Review or run candidate tasks"
    mock_result.warnings = []
    mock_result.errors = []

    with patch("core.dev_planner.StrictDevPlanner.plan_goal", return_value=mock_result) as mock_plan:
        handle_command("dev", "Build something", ctx)
        mock_plan.assert_called_once()

    output = console.file.getvalue()
    assert "planned" in output
    assert "task-001" in output


def test_dev_plan_explicit_goal_calls_planner():
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    mock_result = MagicMock()
    mock_result.status = "planned"
    mock_result.run_id = "run-1"
    mock_result.candidate_count = 1
    mock_result.valid_task_ids = ["task-002"]
    mock_result.invalid_candidate_count = 0
    mock_result.next_action = "Review or run candidate tasks"
    mock_result.warnings = []
    mock_result.errors = []

    with patch("core.dev_planner.StrictDevPlanner.plan_goal", return_value=mock_result) as mock_plan:
        handle_command("dev", "--plan Build something explicit", ctx)
        mock_plan.assert_called_once()

    output = console.file.getvalue()
    assert "planned" in output
    assert "task-002" in output


def test_help_includes_dev():
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("help", "", ctx)
    output = console.file.getvalue()
    assert "/dev" in output


def test_dev_flask_goal_does_not_invent_app_py(monkeypatch):
    """If the planner does not return app.py, it must not appear."""
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    mock_result = MagicMock()
    mock_result.status = "planned"
    mock_result.run_id = "run-1"
    mock_result.candidate_count = 1
    mock_result.valid_task_ids = ["task-001"]
    mock_result.invalid_candidate_count = 0
    mock_result.next_action = "Review"
    mock_result.warnings = []
    mock_result.errors = []

    with patch("core.dev_planner.StrictDevPlanner.plan_goal", return_value=mock_result) as mock_plan:
        handle_command("dev", "Create a Flask image upload service", ctx)
        call_args = mock_plan.call_args
        goal = call_args[1]["goal"] if call_args[1] else call_args[0][0]
        assert "Flask" in goal

    output = console.file.getvalue()
    assert "app.py" not in output
