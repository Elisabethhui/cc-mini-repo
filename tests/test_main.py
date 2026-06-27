import sys
from unittest.mock import MagicMock, patch, PropertyMock
from core.engine import Engine, AbortedError
from core.bootstrap import bootstrap_workspace, doctor_workspace
from core.tools.base import Tool, ToolResult
from core.permissions import PermissionChecker


class DummyTool(Tool):
    name = "Dummy"
    description = "A dummy tool for testing"
    input_schema = {
        "type": "object",
        "properties": {"msg": {"type": "string"}},
        "required": ["msg"],
    }

    def execute(self, msg: str) -> ToolResult:
        return ToolResult(content=f"got: {msg}")


def _make_text_stream(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text

    final_msg = MagicMock()
    final_msg.content = [block]

    stream = MagicMock()
    stream.__enter__ = MagicMock(return_value=stream)
    stream.__exit__ = MagicMock(return_value=False)
    stream.text_stream = iter([text])
    stream.get_final_message = MagicMock(return_value=final_msg)
    return stream


def _make_engine():
    return Engine(
        tools=[DummyTool()],
        system_prompt="test",
        permission_checker=PermissionChecker(auto_approve=True),
    )


class _FakeEscListener:
    """A no-op replacement for EscListener that doesn't touch the terminal."""
    pressed = False

    def __init__(self, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass

    def pause(self):
        pass

    def resume(self):
        pass

    def check_esc_nonblocking(self):
        return False


@patch("core.main.EscListener", _FakeEscListener)
def test_run_query_prints_text(capsys):
    """run_query should print text events to stdout in print_mode."""
    from core.main import run_query

    engine = _make_engine()
    with patch.object(engine._client, "stream_messages", return_value=_make_text_stream("hello world")):
        run_query(engine, "hi", print_mode=True)

    captured = capsys.readouterr()
    assert "hello world" in captured.out


@patch("core.main.EscListener", _FakeEscListener)
def test_run_query_handles_tool_call_event():
    """run_query should display tool call info via rich console."""
    from core.main import run_query

    engine = _make_engine()

    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = "tu_1"
    tool_block.name = "Dummy"
    tool_block.input = {"msg": "test"}

    first_final = MagicMock()
    first_final.content = [tool_block]
    first_stream = MagicMock()
    first_stream.__enter__ = MagicMock(return_value=first_stream)
    first_stream.__exit__ = MagicMock(return_value=False)
    first_stream.text_stream = iter([])
    first_stream.get_final_message = MagicMock(return_value=first_final)

    second_stream = _make_text_stream("done")

    with patch.object(engine._client, "stream_messages", side_effect=[first_stream, second_stream]):
        run_query(engine, "use tool", print_mode=True)


@patch("core.main.EscListener", _FakeEscListener)
def test_run_query_handles_keyboard_interrupt():
    """run_query should gracefully handle KeyboardInterrupt."""
    from core.main import run_query

    engine = _make_engine()

    def raise_interrupt(*a, **kw):
        raise KeyboardInterrupt()

    with patch.object(engine._client, "stream_messages", side_effect=raise_interrupt):
        run_query(engine, "hi", print_mode=True)
    # Should not propagate the exception


def test_init_command_bootstraps_workspace(tmp_path, capsys):
    """cc-mini init should create the bootstrap scaffold in the current workspace."""
    from core.main import main

    with patch.object(sys, "argv", ["cc-mini", "init"]), \
         patch("core.main.Path.cwd", return_value=tmp_path), \
         patch("core.main.bootstrap_workspace", wraps=bootstrap_workspace) as mocked_bootstrap:
        main()

    mocked_bootstrap.assert_called_once_with(tmp_path)

    index_file = tmp_path / ".cc-mini" / "wiki" / "index.md"
    assert index_file.exists()
    assert index_file.read_text(encoding="utf-8").startswith("# cc-mini Phase 1 Workspace")

    output = capsys.readouterr().out
    assert "Initialized cc-mini workspace" in output
    assert "Next: run `cc-mini` to open the REPL." in output


def test_init_command_reports_already_present(tmp_path, capsys):
    """cc-mini init should tell the user when the scaffold already exists."""
    from core.main import main

    bootstrap_workspace(tmp_path)

    with patch.object(sys, "argv", ["cc-mini", "init"]), \
         patch("core.main.Path.cwd", return_value=tmp_path), \
         patch("core.main.bootstrap_workspace", wraps=bootstrap_workspace) as mocked_bootstrap:
        main()

    mocked_bootstrap.assert_called_once_with(tmp_path)
    output = capsys.readouterr().out
    assert "already present" in output
def test_doctor_command_reports_missing_workspace(tmp_path, capsys):
    """cc-mini doctor should report a missing workspace without modifying files."""
    from core.main import main

    with patch.object(sys, "argv", ["cc-mini", "doctor"]), \
         patch("core.main.Path.cwd", return_value=tmp_path), \
         patch("core.main.doctor_workspace", wraps=doctor_workspace) as mocked_doctor:
        main()

    mocked_doctor.assert_called_once_with(tmp_path)
    assert not (tmp_path / ".cc-mini").exists()

    output = capsys.readouterr().out
    assert "Workspace is missing the cc-mini scaffold." in output
    assert "Run `cc-mini init` to create it." in output


def test_doctor_command_reports_initialized_workspace(tmp_path, capsys):
    """cc-mini doctor should report a ready workspace clearly."""
    from core.main import main

    bootstrap_workspace(tmp_path)

    with patch.object(sys, "argv", ["cc-mini", "doctor"]), \
         patch("core.main.Path.cwd", return_value=tmp_path), \
         patch("core.main.doctor_workspace", wraps=doctor_workspace) as mocked_doctor:
        main()

    mocked_doctor.assert_called_once_with(tmp_path)
    output = capsys.readouterr().out
    assert "Workspace is initialized and ready." in output
    assert "Run `cc-mini` to open the REPL." in output


def test_doctor_command_reports_stale_workspace(tmp_path, capsys):
    """cc-mini doctor should identify a stale scaffold."""
    from core.main import main

    bootstrap_workspace(tmp_path)
    (tmp_path / ".cc-mini" / "wiki" / "index.md").unlink()

    with patch.object(sys, "argv", ["cc-mini", "doctor"]), \
         patch("core.main.Path.cwd", return_value=tmp_path), \
         patch("core.main.doctor_workspace", wraps=doctor_workspace) as mocked_doctor:
        main()

    mocked_doctor.assert_called_once_with(tmp_path)
    output = capsys.readouterr().out
    assert "Workspace scaffold is stale or incomplete." in output
    assert "Missing:" in output
    assert "wiki/index.md" in output


def test_run_command_strips_explicit_run_prefix_and_preserves_mode(tmp_path):
    """cc-mini run should strip the explicit run prefix and honor --mode."""
    from core.main import main
    from core.config import RunMode

    captured = {}

    def fake_run_query(engine, user_input, print_mode, permissions=None, quiet=False):
        captured["user_input"] = user_input
        captured["print_mode"] = print_mode

    with patch.object(sys, "argv", ["cc-mini", "run", "--mode", "wiki_strict", "hello"]), \
         patch("core.main.Path.cwd", return_value=tmp_path), \
         patch("core.main.run_query", side_effect=fake_run_query), \
         patch("core.main.get_run_mode", return_value=RunMode.WIKI_STRICT) as mocked_run_mode, \
         patch("core.main.ensure_memory_dir"), \
         patch("core.main.SessionStore") as mocked_session_store:
        mocked_session_store.return_value = object()
        main()

    mocked_run_mode.assert_called_once_with("wiki_strict")
    assert captured["user_input"] == "hello"
    assert captured["print_mode"] is False


def test_wiki_strict_startup_is_lazy(tmp_path, capsys):
    """wiki_strict startup should not auto-ingest or start the watcher before prompting."""
    from core.main import main

    with patch.object(sys, "argv", ["cc-mini", "run", "--mode", "wiki_strict"]), \
         patch("core.main.Path.cwd", return_value=tmp_path), \
         patch("core.main.ensure_memory_dir"), \
         patch("core.main.SessionStore") as mocked_session_store, \
         patch("core.main._bordered_prompt", side_effect=EOFError):
        mocked_session_store.return_value.session_id = "session-1"
        mocked_session_store.return_value.mode = "standard"
        main()

    output = capsys.readouterr().out
    assert "analysis-first" in output
    assert "正在扫描工作区" not in output


def test_standard_startup_stays_quiet_about_wiki_strict(tmp_path, capsys):
    """standard mode should not emit wiki_strict-specific startup text."""
    from core.main import main

    with patch.object(sys, "argv", ["cc-mini", "run", "--mode", "standard"]), \
         patch("core.main.Path.cwd", return_value=tmp_path), \
         patch("core.main.ensure_memory_dir"), \
         patch("core.main.SessionStore") as mocked_session_store, \
         patch("core.main._bordered_prompt", side_effect=EOFError):
        mocked_session_store.return_value.session_id = "session-1"
        mocked_session_store.return_value.mode = "standard"
        main()

    output = capsys.readouterr().out
    assert "analysis-first" not in output
    assert "wiki_strict will scan only when you explicitly invoke /scan, /prime, or /plan." not in output


def test_standard_startup_skips_wiki_strict_banner(tmp_path, capsys):
    """standard startup should reach the normal REPL path without wiki_strict banners."""
    from core.main import main

    with patch.object(sys, "argv", ["cc-mini", "run", "--mode", "standard"]), \
         patch("core.main.Path.cwd", return_value=tmp_path), \
         patch("core.main.ensure_memory_dir"), \
         patch("core.main.SessionStore") as mocked_session_store, \
         patch("core.main._bordered_prompt", side_effect=EOFError) as mocked_prompt:
        mocked_session_store.return_value.session_id = "session-1"
        mocked_session_store.return_value.mode = "standard"
        main()

    assert mocked_prompt.call_count == 1
    output = capsys.readouterr().out
    assert "analysis-first" not in output
    assert "wiki_strict will scan only" not in output
    assert "cc-mini" in output


def test_mode_specific_system_prompt_differs_by_run_mode(tmp_path):
    from core.config import RunMode
    from core.context import build_mode_system_prompt

    standard_prompt = build_mode_system_prompt(run_mode=RunMode.STANDARD, cwd=str(tmp_path))
    wiki_prompt = build_mode_system_prompt(run_mode=RunMode.WIKI_STRICT, cwd=str(tmp_path))

    assert "WIKI_STRICT Flow-State Mode" not in standard_prompt
    assert "WIKI_STRICT Flow-State Mode" in wiki_prompt


def test_main_auto_approve_env_var_affects_permission_checker(tmp_path, monkeypatch):
    """CC_MINI_AUTO_APPROVE=true should propagate to PermissionChecker in main()."""
    from core.main import main
    from core.permissions import PermissionChecker

    monkeypatch.setenv("CC_MINI_AUTO_APPROVE", "true")
    captured_auto_approve = []

    original_init = PermissionChecker.__init__

    def capturing_init(self, auto_approve=False, **kwargs):
        captured_auto_approve.append(auto_approve)
        original_init(self, auto_approve=auto_approve, **kwargs)

    with patch.object(sys, "argv", ["cc-mini", "run", "--mode", "standard"]), \
         patch("core.main.Path.cwd", return_value=tmp_path), \
         patch("core.main.ensure_memory_dir"), \
         patch("core.main.SessionStore") as mocked_session_store, \
         patch("core.main._bordered_prompt", side_effect=EOFError), \
         patch.object(PermissionChecker, "__init__", capturing_init):
        mocked_session_store.return_value.session_id = "session-1"
        mocked_session_store.return_value.mode = "standard"
        main()

    # There may be multiple PermissionChecker instances (main + worker).
    # At least one should have auto_approve=True from the env var.
    assert any(captured_auto_approve), f"Expected at least one auto_approve=True, got {captured_auto_approve}"


def test_main_auto_approve_cli_flag_overrides_env(tmp_path, monkeypatch):
    """--auto-approve CLI flag should still work and override env var default."""
    from core.main import main
    from core.permissions import PermissionChecker

    monkeypatch.setenv("CC_MINI_AUTO_APPROVE", "false")
    captured_auto_approve = []

    original_init = PermissionChecker.__init__

    def capturing_init(self, auto_approve=False, **kwargs):
        captured_auto_approve.append(auto_approve)
        original_init(self, auto_approve=auto_approve, **kwargs)

    with patch.object(sys, "argv", ["cc-mini", "run", "--auto-approve"]), \
         patch("core.main.Path.cwd", return_value=tmp_path), \
         patch("core.main.ensure_memory_dir"), \
         patch("core.main.SessionStore") as mocked_session_store, \
         patch("core.main._bordered_prompt", side_effect=EOFError), \
         patch.object(PermissionChecker, "__init__", capturing_init):
        mocked_session_store.return_value.session_id = "session-1"
        mocked_session_store.return_value.mode = "standard"
        main()

    assert any(captured_auto_approve), f"Expected at least one auto_approve=True from CLI, got {captured_auto_approve}"
