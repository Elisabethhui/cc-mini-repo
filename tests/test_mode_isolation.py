from __future__ import annotations

import sys
from unittest.mock import patch


def test_standard_mode_does_not_emit_wiki_strict_banner(tmp_path, capsys):
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


def test_mode_specific_prompt_separates_standard_and_wiki_strict(tmp_path):
    from core.config import RunMode
    from core.context import build_mode_system_prompt

    standard_prompt = build_mode_system_prompt(run_mode=RunMode.STANDARD, cwd=str(tmp_path))
    wiki_prompt = build_mode_system_prompt(run_mode=RunMode.WIKI_STRICT, cwd=str(tmp_path))

    assert "WIKI_STRICT Flow-State Mode" not in standard_prompt
    assert "WIKI_STRICT Flow-State Mode" in wiki_prompt
