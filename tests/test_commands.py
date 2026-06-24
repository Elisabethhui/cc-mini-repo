from io import StringIO
from unittest.mock import MagicMock

from rich.console import Console

from core.commands import CommandContext, handle_command
from core.wiki.semantic_artifacts import ArtifactRecord, SemanticArtifactStore


def test_help_lists_phase1_and_later_phase_commands():
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
    assert "/scan" in output
    assert "/prime" in output
    assert "/plan" in output
    assert "/task" in output
    assert "/reconcile" in output
    assert "/maintenance" in output
    assert "/close" in output
    assert "/milestone-review" in output
    assert "/workflow-status" in output
    assert "/workflow-init" in output
    assert "/workflow-doctor" in output
    assert "/workflow-test" in output
    assert "confirm with /close confirm" in output.lower()
    assert "read-only" in output.lower()
    assert "Legacy /init_build (later-phase, not Phase 1)" in output
    assert "Later-phase /post_edit demo/stub" in output


def test_reconcile_and_maintenance_are_view_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = SemanticArtifactStore(tmp_path)
    store.save(
        ArtifactRecord(
            artifact_id="drift-1",
            layer="derived",
            kind="drift_note",
            task_id="task-1",
            source="phase3",
            priority=5,
            payload={"note": "entity drifted"},
        )
    )
    store.save(
        ArtifactRecord(
            artifact_id="maint-1",
            layer="derived",
            kind="maintenance_candidate",
            task_id="task-1",
            source="phase3",
            priority=5,
            payload={"reason": "stale semantic snapshot"},
        )
    )

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("reconcile", "", ctx)
    handle_command("maintenance", "", ctx)

    output = console.file.getvalue()
    assert "Reconcile Projection (view-only)" in output
    assert "Maintenance Projection (view-only)" in output
    assert "derived" in output
    assert "manual" in output or "Manual artifacts" in output


def test_workflow_status_command_is_read_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("rules\n", encoding="utf-8")
    (tmp_path / ".ai-dev").mkdir()

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("workflow-status", "", ctx)

    output = console.file.getvalue()
    assert "Workflow status:" in output
    assert "Required Files:" in output
    assert "CodeGraph:" in output
    assert "Git:" in output
    assert not (tmp_path / ".codegraph").exists()


def test_workflow_init_command_supports_dry_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("workflow-init", "--dry-run", ctx)

    output = console.file.getvalue()
    assert "Workflow init dry run" in output
    assert ".ai-dev/README.md" in output
    assert not (tmp_path / ".ai-dev").exists()


def test_workflow_init_command_creates_missing_files_without_overwrite(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    existing = tmp_path / ".ai-dev" / "README.md"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("keep me\n", encoding="utf-8")

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("workflow-init", "", ctx)

    output = console.file.getvalue()
    assert "Workflow init" in output
    assert "Skipped:" in output
    assert ".ai-dev/README.md" in output
    assert ".ai-dev/WORKFLOW.md" in output
    assert existing.read_text(encoding="utf-8") == "keep me\n"
    assert (tmp_path / ".ai-dev" / "WORKFLOW.md").exists()


def test_workflow_doctor_command_is_read_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "AGENTS.md").write_text("rules\n", encoding="utf-8")
    (tmp_path / ".ai-dev" / "README.md").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / ".ai-dev" / "README.md").write_text("readme\n", encoding="utf-8")
    (tmp_path / ".ai-dev" / "WORKFLOW.md").write_text("workflow\n", encoding="utf-8")
    (tmp_path / ".ai-dev" / "skills").mkdir()
    (tmp_path / ".ai-dev" / "templates").mkdir()
    (tmp_path / ".ai-dev" / "templates" / "CURRENT_TASK.md").write_text("# Task\n", encoding="utf-8")

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    handle_command("workflow-doctor", "", ctx)

    output = console.file.getvalue()
    assert "Context-Bounded Workflow Doctor" in output
    assert "Required Files:" in output
    assert "Local Artifacts:" in output
    assert "Markdown:" in output
    assert "CodeGraph:" in output
    assert "Decision:" in output
    assert not (tmp_path / ".codegraph").exists()
    assert not (tmp_path / ".ai-dev" / "tasks").exists()


def test_workflow_test_command_recommends_passed_files_without_running_tests(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    testing = tmp_path / ".ai-dev" / "TESTING.md"
    testing.parent.mkdir(parents=True, exist_ok=True)
    testing.write_text(
        "# Testing Registry\n\n"
        "- `src/core/commands.py` -> `tests/test_commands.py`\n",
        encoding="utf-8",
    )

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    run_calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):
        run_calls.append(tuple(args[0]))
        raise AssertionError("workflow-test should not execute pytest")

    monkeypatch.setattr("core.commands.subprocess.run", fake_run)

    handle_command("workflow-test", "src/core/commands.py", ctx)

    output = console.file.getvalue()
    assert "Test Selector" in output
    assert "Confidence: medium" in output
    assert "pytest tests/test_commands.py -v" in output
    assert "Warnings:" in output
    assert run_calls == []


def test_workflow_test_command_uses_current_diff_read_only(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    testing = tmp_path / ".ai-dev" / "TESTING.md"
    testing.parent.mkdir(parents=True, exist_ok=True)
    testing.write_text(
        "# Testing Registry\n\n"
        "- `src/core/commands.py` -> `tests/test_commands.py`\n",
        encoding="utf-8",
    )

    console = Console(file=StringIO())
    ctx = CommandContext(
        engine=MagicMock(),
        session_store=MagicMock(),
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )

    class Result:
        returncode = 0
        stdout = " M src/core/commands.py\n"
        stderr = ""

    monkeypatch.setattr("core.commands.subprocess.run", lambda *args, **kwargs: Result())

    handle_command("workflow-test", "", ctx)

    output = console.file.getvalue()
    assert "Test Selector" in output
    assert "pytest tests/test_commands.py -v" in output
    assert "Confidence: medium" in output
    assert "codeintel unavailable; using fallback rules" in output
