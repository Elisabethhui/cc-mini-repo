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
