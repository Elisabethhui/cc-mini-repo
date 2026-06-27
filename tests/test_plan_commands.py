from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from rich.console import Console

from core.commands import CommandContext, handle_command
from core.plan_graph import PlanGraph, TaskNode
from core.runtime_state import RuntimeStateStore


@pytest.fixture
def ctx(monkeypatch, tmp_path):
    """Create a CommandContext wired to tmp_path as cwd."""
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    return CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )


class TestPlanInit:
    def test_plan_init_creates_plan_graph_json(self, ctx, tmp_path):
        handle_command("plan-init", "Build a CLI tool", ctx)

        output = ctx.console.file.getvalue()
        assert "Plan initialized" in output
        assert "Build a CLI tool" in output

        # Verify plan-graph.json was written
        runtime_dir = tmp_path / ".ai-dev" / "runtime"
        run_dirs = list(runtime_dir.iterdir())
        assert len(run_dirs) == 1

        plan_path = run_dirs[0] / "plan-graph.json"
        assert plan_path.exists()

        graph = PlanGraph.from_json(plan_path.read_text(encoding="utf-8"))
        assert graph.goal == "Build a CLI tool"
        assert graph.phase == "intake"
        assert graph.run_id == run_dirs[0].name

    def test_plan_init_without_args_shows_usage(self, ctx):
        handle_command("plan-init", "", ctx)
        output = ctx.console.file.getvalue()
        assert "Usage: /plan-init <goal>" in output

    def test_plan_init_updates_runtime_state(self, ctx, tmp_path):
        handle_command("plan-init", "Test goal", ctx)

        runtime_dir = tmp_path / ".ai-dev" / "runtime"
        run_dirs = list(runtime_dir.iterdir())
        store = RuntimeStateStore(str(tmp_path), run_id=run_dirs[0].name)
        state = store.load_state()
        assert state["goal"] == "Test goal"
        assert state["phase"] == "intake"

    def test_plan_init_empty_repo(self, ctx, tmp_path):
        """plan-init should work even when the repo is completely empty."""
        handle_command("plan-init", "Empty repo goal", ctx)

        runtime_dir = tmp_path / ".ai-dev" / "runtime"
        assert runtime_dir.exists()
        run_dirs = list(runtime_dir.iterdir())
        assert len(run_dirs) == 1

        plan_path = run_dirs[0] / "plan-graph.json"
        assert plan_path.exists()


class TestPlanStatus:
    def test_plan_status_shows_current_plan(self, ctx, tmp_path):
        # First init a plan
        handle_command("plan-init", "My project", ctx)
        ctx.console.file.truncate(0)
        ctx.console.file.seek(0)

        handle_command("plan-status", "", ctx)
        output = ctx.console.file.getvalue()
        assert "Plan Status" in output
        assert "My project" in output
        assert "intake" in output
        assert "Next Action" in output

    def test_plan_status_no_runs(self, ctx):
        handle_command("plan-status", "", ctx)
        output = ctx.console.file.getvalue()
        assert "No planning runs found" in output

    def test_plan_status_with_decisions_and_questions(self, ctx, tmp_path):
        handle_command("plan-init", "Project with decisions", ctx)

        runtime_dir = tmp_path / ".ai-dev" / "runtime"
        run_dirs = list(runtime_dir.iterdir())
        plan_path = run_dirs[0] / "plan-graph.json"
        graph = PlanGraph.from_json(plan_path.read_text(encoding="utf-8"))
        graph.add_decision("Use Python 3.11")
        graph.add_open_question("Which database?")
        graph.add_risk("Third-party API instability")
        plan_path.write_text(graph.to_json(), encoding="utf-8")

        ctx.console.file.truncate(0)
        ctx.console.file.seek(0)

        handle_command("plan-status", "", ctx)
        output = ctx.console.file.getvalue()
        assert "Decisions (1):" in output
        assert "Use Python 3.11" in output
        assert "Open Questions (1):" in output
        assert "Which database?" in output
        assert "Risks (1):" in output
        assert "Third-party API instability" in output

    def test_plan_status_with_tasks(self, ctx, tmp_path):
        handle_command("plan-init", "Project with tasks", ctx)

        runtime_dir = tmp_path / ".ai-dev" / "runtime"
        run_dirs = list(runtime_dir.iterdir())
        plan_path = run_dirs[0] / "plan-graph.json"
        graph = PlanGraph.from_json(plan_path.read_text(encoding="utf-8"))
        graph.add_task(TaskNode(id="task-1", goal="Set up repo"))
        graph.add_task(TaskNode(id="task-2", goal="Add tests", depends_on=["task-1"]))
        plan_path.write_text(graph.to_json(), encoding="utf-8")

        ctx.console.file.truncate(0)
        ctx.console.file.seek(0)

        handle_command("plan-status", "", ctx)
        output = ctx.console.file.getvalue()
        assert "Tasks:" in output
        assert "2 total, 1 ready" in output
        assert "task-1" in output
        assert "Set up repo" in output


class TestPlanExport:
    def test_plan_export_creates_artifact(self, ctx, tmp_path):
        # First init a plan
        handle_command("plan-init", "Export test", ctx)
        ctx.console.file.truncate(0)
        ctx.console.file.seek(0)

        handle_command("plan-export", "", ctx)
        output = ctx.console.file.getvalue()
        assert "Plan exported" in output
        assert "Export test" in output

        # Verify artifact was written
        runtime_dir = tmp_path / ".ai-dev" / "runtime"
        run_dirs = list(runtime_dir.iterdir())
        store = RuntimeStateStore(str(tmp_path), run_id=run_dirs[0].name)
        assert "plan-export.md" in store.list_artifacts()

    def test_plan_export_no_runs(self, ctx):
        handle_command("plan-export", "", ctx)
        output = ctx.console.file.getvalue()
        assert "No planning runs found" in output

    def test_plan_export_content(self, ctx, tmp_path):
        handle_command("plan-init", "Content test", ctx)

        runtime_dir = tmp_path / ".ai-dev" / "runtime"
        run_dirs = list(runtime_dir.iterdir())
        plan_path = run_dirs[0] / "plan-graph.json"
        graph = PlanGraph.from_json(plan_path.read_text(encoding="utf-8"))
        graph.add_decision("Use FastAPI")
        graph.add_open_question("Auth provider?")
        graph.add_module("api")
        graph.add_task(TaskNode(id="t1", goal="Bootstrap"))
        plan_path.write_text(graph.to_json(), encoding="utf-8")

        ctx.console.file.truncate(0)
        ctx.console.file.seek(0)

        handle_command("plan-export", "", ctx)
        output = ctx.console.file.getvalue()
        assert "# Plan Export:" in output
        assert "Content test" in output
        assert "## Decisions" in output
        assert "Use FastAPI" in output
        assert "## Open Questions" in output
        assert "Auth provider?" in output
        assert "## Modules" in output
        assert "api" in output
        assert "## Tasks" in output
        assert "(ready) t1: Bootstrap" in output


class TestPlanHelp:
    def test_plan_commands_in_help(self, ctx):
        handle_command("help", "", ctx)
        output = ctx.console.file.getvalue()
        assert "/plan-init" in output
        assert "/plan-status" in output
        assert "/plan-export" in output
        assert "Initialize a new planning run" in output
        assert "Show current planning phase" in output
        assert "Export a compact planning summary" in output
