from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock

from rich.console import Console

from core.commands import CommandContext, _cmd_plan_wiki, _cmd_prime, _cmd_scan
from core.config import AppConfig
from core.bootstrap import bootstrap_workspace


def _make_context() -> CommandContext:
    buffer = StringIO()
    return CommandContext(
        engine=MagicMock(),
        session_store=None,
        compact_service=MagicMock(),
        console=Console(file=buffer, force_terminal=False, color_system=None, width=120),
        app_config=AppConfig(
            provider="anthropic",
            api_key=None,
            base_url=None,
            model="claude-sonnet-4-20250514",
            max_tokens=32000,
        ),
    )


def test_phase1_analysis_chain_scan_prime_plan(tmp_path, monkeypatch):
    (tmp_path / "sample.py").write_text(
        "def add(a, b):\n"
        "    \"\"\"Add two numbers.\"\"\"\n"
        "    return a + b\n",
        encoding="utf-8",
    )
    monkeypatch.chdir(tmp_path)
    bootstrap_workspace(tmp_path)

    ctx = _make_context()

    _cmd_scan(ctx, "")
    _cmd_prime(ctx, "task-1 sample.py")
    monkeypatch.setenv("CC_MINI_MODE", "wiki_strict")
    _cmd_plan_wiki(ctx, "task-1")

    output = ctx.console.file.getvalue()
    assert "Scan complete. Wiki entities updated." in output
    assert "TaskPack primed and saved" in output
    assert "Plan generated. Ready for review before patch phase." in output
