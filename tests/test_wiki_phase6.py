from io import StringIO
from unittest.mock import MagicMock

from rich.console import Console

from core.commands import CommandContext, handle_command
from core.wiki.closeout import CloseoutRecord, CloseoutStore


def _make_ctx(console: Console) -> CommandContext:
    return CommandContext(
        engine=MagicMock(),
        session_store=None,
        compact_service=MagicMock(),
        console=console,
        app_config=MagicMock(),
    )


def test_close_requires_confirm_before_commit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = _make_ctx(console)
    invocations: list[tuple[str, str]] = []

    monkeypatch.setattr(
        "core.commands._invoke_skill",
        lambda command_ctx, name, args="": invocations.append((name, args)) or True,
    )

    handle_command("close", "", ctx)
    output = console.file.getvalue()

    assert "Confirm with /close confirm" in output
    assert "ready for audit" not in output.lower()
    assert ctx.pending_query is not None
    assert ctx.pending_closeout is not None
    assert any((tmp_path / ".cc-mini" / "wiki" / "reports" / "closeout").glob("*.json"))
    assert invocations == []

    handle_command("close", "confirm", ctx)
    output = console.file.getvalue()

    assert "closeout finalized" in output.lower()
    assert "commit" in output.lower()
    assert invocations == [("test", ""), ("review", ""), ("commit", "")]
    assert ctx.pending_closeout is None
    assert ctx.pending_query is None


def test_close_cancel_exits_cleanly_without_git_mutation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = _make_ctx(console)
    invocations: list[tuple[str, str]] = []

    monkeypatch.setattr(
        "core.commands._invoke_skill",
        lambda command_ctx, name, args="": invocations.append((name, args)) or True,
    )

    handle_command("close", "", ctx)
    handle_command("close", "cancel", ctx)

    output = console.file.getvalue()
    assert "cancel" in output.lower()
    assert ctx.pending_closeout is None
    assert ctx.pending_query is None
    assert invocations == []


def test_close_stops_when_verification_failed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = _make_ctx(console)
    invocations: list[tuple[str, str]] = []

    monkeypatch.setattr(
        "core.commands._invoke_skill",
        lambda command_ctx, name, args="": invocations.append((name, args)) or True,
    )

    handle_command("close", "", ctx)
    ctx.pending_closeout.verification_status = "failed"
    ctx.pending_closeout.review_status = "approved"

    handle_command("close", "confirm", ctx)

    output = console.file.getvalue()
    assert "verification" in output.lower()
    assert "failed" in output.lower()
    assert invocations == []
    assert ctx.pending_closeout is not None


def test_milestone_review_is_read_only_when_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    console = Console(file=StringIO())
    ctx = _make_ctx(console)

    handle_command("milestone-review", "", ctx)

    output = console.file.getvalue()
    assert "No closeout record found" in output
    assert "/close" in output
    assert ctx.pending_query is None
    assert ctx.pending_closeout is None


def test_milestone_review_reports_ready_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = CloseoutStore(tmp_path)
    store.save(
        CloseoutRecord(
            task_id="task-1",
            phase_name="Phase 6",
            verification_status="passed",
            review_status="approved",
            commit_status="recorded",
            commit_hash="abc1234",
            ready_for_audit=True,
            residual_risks=[],
        )
    )

    console = Console(file=StringIO())
    ctx = _make_ctx(console)

    handle_command("milestone-review", "", ctx)

    output = console.file.getvalue()
    assert "Milestone Review" in output
    assert "Ready for audit" in output
    assert "Verification Status: passed" in output
    assert "Review Status: approved" in output
    assert "Commit Hash: `abc1234`" in output
    assert "- None" in output
    assert ctx.pending_query is None
    assert ctx.pending_closeout is None


def test_milestone_review_reports_not_ready_state(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    store = CloseoutStore(tmp_path)
    store.save(
        CloseoutRecord(
            task_id="task-1",
            phase_name="Phase 6",
            verification_status="passed",
            review_status="approved",
            commit_status="pending",
            commit_hash=None,
            ready_for_audit=False,
            residual_risks=["commit confirmation still pending"],
        )
    )

    console = Console(file=StringIO())
    ctx = _make_ctx(console)

    handle_command("milestone-review", "", ctx)

    output = console.file.getvalue()
    assert "Not ready for audit" in output
    assert "Commit Status: pending" in output
    assert "Commit Hash: `None`" in output
    assert "commit confirmation still pending" in output
    assert ctx.pending_query is None
    assert ctx.pending_closeout is None
