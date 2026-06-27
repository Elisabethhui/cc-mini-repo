from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock

from rich.console import Console

from core.commands import CommandContext, handle_command
from core.runtime_state import RuntimeStateStore


def test_workflow_run_without_args_shows_usage(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("workflow-run", "", ctx)
    output = console.file.getvalue()
    assert "Usage:" in output
    assert "/workflow-run" in output


def test_workflow_run_dry_run_creates_runtime_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("workflow-run", "--dry-run Implement feature X", ctx)
    output = console.file.getvalue()

    # Runtime state should be created
    runtime_dir = tmp_path / ".ai-dev" / "runtime"
    assert runtime_dir.exists()
    run_dirs = list(runtime_dir.iterdir())
    assert len(run_dirs) == 1

    store = RuntimeStateStore(str(tmp_path), run_id=run_dirs[0].name)
    state = store.load_state()
    assert state["goal"] == "Implement feature X"
    assert state["phase"] == "intake"
    assert state["next_action"] == "Start intake"

    assert "Dry-run plan created:" in output
    assert "Implement feature X" in output


def test_workflow_run_dry_run_creates_plan_graph(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("workflow-run", "--dry-run Test goal", ctx)

    runtime_dir = tmp_path / ".ai-dev" / "runtime"
    run_dirs = list(runtime_dir.iterdir())
    plan_path = run_dirs[0] / "plan-graph.json"
    assert plan_path.exists()

    from core.plan_graph import PlanGraph
    graph = PlanGraph.from_json(plan_path.read_text(encoding="utf-8"))
    assert graph.goal == "Test goal"
    assert graph.phase == "intake"


def test_workflow_run_dry_run_creates_context_pack(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("workflow-run", "--dry-run Some goal", ctx)

    packs_dir = tmp_path / ".ai-dev" / "context-packs"
    assert packs_dir.exists()
    pack_files = list(packs_dir.iterdir())
    assert len(pack_files) == 1
    assert pack_files[0].suffix == ".md"


def test_workflow_run_outputs_budget_and_warnings(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("workflow-run", "--dry-run Build feature", ctx)
    output = console.file.getvalue()

    assert "Tokens:" in output
    assert "Budget:" in output
    assert "Planned Phases:" in output
    assert "intake" in output
    assert "plan" in output
    assert "review" in output


def test_workflow_run_dry_run_does_not_modify_product_code(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    # Create a fake product file
    src_dir = tmp_path / "src" / "core"
    src_dir.mkdir(parents=True)
    (src_dir / "main.py").write_text("# original\n", encoding="utf-8")

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("workflow-run", "--dry-run Build feature", ctx)

    # Product code should remain unchanged
    assert (src_dir / "main.py").read_text(encoding="utf-8") == "# original\n"


def test_workflow_run_dry_run_does_not_run_tests(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    run_calls = []

    def fake_run(*args, **kwargs):
        run_calls.append(args)

    monkeypatch.setattr("core.commands.subprocess.run", fake_run)

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )
    handle_command("workflow-run", "--dry-run Build feature", ctx)

    # No pytest or test execution
    assert not any("pytest" in str(c) for c in run_calls)
