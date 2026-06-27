from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock

from rich.console import Console

from core.commands import CommandContext, handle_command
from core.plan_graph import PlanGraph
from core.runtime_state import RuntimeStateStore


def test_workflow_pack_without_args_shows_usage(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("workflow-pack", "", ctx)
    output = console.file.getvalue()
    assert "Usage:" in output
    assert "/workflow-pack" in output


def test_workflow_pack_generates_pack_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("workflow-pack", "Implement feature X", ctx)
    output = console.file.getvalue()

    packs_dir = tmp_path / ".ai-dev" / "context-packs"
    assert packs_dir.exists()
    pack_files = list(packs_dir.iterdir())
    assert len(pack_files) == 1
    assert pack_files[0].suffix == ".md"
    assert "Context pack generated:" in output
    assert "Implement feature X" in output


def test_workflow_pack_uses_plan_graph_when_exists(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    # Create a plan graph in runtime state
    store = RuntimeStateStore(str(tmp_path), run_id="test-run-001")
    graph = PlanGraph(
        run_id="test-run-001",
        goal="Build a todo app",
        phase="design",
        next_action="Design data model",
        decisions=["Use SQLite"],
    )
    plan_path = store.base_dir / "plan-graph.json"
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(graph.to_json(), encoding="utf-8")

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("workflow-pack", "Build a todo app", ctx)
    output = console.file.getvalue()

    packs_dir = tmp_path / ".ai-dev" / "context-packs"
    pack_files = list(packs_dir.iterdir())
    assert len(pack_files) == 1
    assert pack_files[0].name == "test-run-001.md"
    content = pack_files[0].read_text(encoding="utf-8")
    assert "Build a todo app" in content
    assert "Use SQLite" in content
    assert "Context pack generated:" in output


def test_workflow_pack_skips_code_retrieval_in_empty_repo(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    # No src/ or .codegraph exists
    handle_command("workflow-pack", "Some goal", ctx)
    output = console.file.getvalue()

    packs_dir = tmp_path / ".ai-dev" / "context-packs"
    pack_files = list(packs_dir.iterdir())
    assert len(pack_files) == 1
    content = pack_files[0].read_text(encoding="utf-8")
    # Should not contain retrieval sections when no code exists
    assert "## Relevant Code" not in content
    assert "Context pack generated:" in output


def test_workflow_pack_outputs_budget_report(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("workflow-pack", "Test goal", ctx)
    output = console.file.getvalue()
    assert "Tokens:" in output
    assert "State:" in output
