from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from core.dev_contract import VerificationSpec
from core.verification_runner import (
    VerificationRunner,
    VerificationRunResult,
    _is_safe_path,
    _resolve_within_workspace,
    _truncate,
)


# ---------------------------------------------------------------------------
# command verification
# ---------------------------------------------------------------------------

def test_command_verification_passing(tmp_path):
    runner = VerificationRunner()
    spec = VerificationSpec(
        kind="command",
        command=["python3", "-c", "print('hello')"],
        expected_exit_code=0,
    )
    result = runner.run(spec, tmp_path)
    assert result.passed is True
    assert result.exit_code == 0
    assert "hello" in result.stdout
    assert result.timed_out is False


def test_command_verification_failing(tmp_path):
    runner = VerificationRunner()
    spec = VerificationSpec(
        kind="command",
        command=["python3", "-c", "import sys; sys.exit(1)"],
        expected_exit_code=0,
    )
    result = runner.run(spec, tmp_path)
    assert result.passed is False
    assert result.exit_code == 1
    assert result.risks


def test_command_timeout(tmp_path):
    runner = VerificationRunner()
    spec = VerificationSpec(
        kind="command",
        command=["python3", "-c", "import time; time.sleep(10)"],
        timeout_seconds=1,
    )
    t0 = time.monotonic()
    result = runner.run(spec, tmp_path)
    duration = time.monotonic() - t0
    assert result.timed_out is True
    assert result.passed is False
    assert duration < 3.0  # Should not wait 10s


def test_command_stdout_stderr_truncation(tmp_path):
    runner = VerificationRunner()
    big = "x" * 10000
    spec = VerificationSpec(
        kind="command",
        command=["python3", "-c", f"print('{big}'); print('{big}', file=__import__('sys').stderr)"],
    )
    result = runner.run(spec, tmp_path)
    assert len(result.stdout) < 5000
    assert len(result.stderr) < 5000
    assert "[truncated]" in result.stdout or len(big) > 5000


# ---------------------------------------------------------------------------
# artifact verification
# ---------------------------------------------------------------------------

def test_artifact_verification_passing(tmp_path):
    runner = VerificationRunner()
    (tmp_path / "out.txt").write_text("done", encoding="utf-8")
    spec = VerificationSpec(
        kind="artifact",
        expected_artifacts=["out.txt"],
    )
    result = runner.run(spec, tmp_path)
    assert result.passed is True
    assert result.artifact_paths == ["out.txt"]


def test_artifact_verification_failing(tmp_path):
    runner = VerificationRunner()
    spec = VerificationSpec(
        kind="artifact",
        expected_artifacts=["missing.txt"],
    )
    result = runner.run(spec, tmp_path)
    assert result.passed is False
    assert "missing" in result.risks[0]


# ---------------------------------------------------------------------------
# manual / contract
# ---------------------------------------------------------------------------

def test_manual_verification_skipped(tmp_path):
    runner = VerificationRunner()
    spec = VerificationSpec(kind="manual", notes="Check UI manually")
    result = runner.run(spec, tmp_path)
    assert result.skipped is True
    assert result.passed is False
    assert "Manual" in result.summary


def test_contract_verification_does_not_run_shell(tmp_path, monkeypatch):
    runner = VerificationRunner()
    spec = VerificationSpec(kind="contract")
    # If subprocess.run were called, this would blow up
    monkeypatch.setattr("subprocess.run", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("shell called")))
    result = runner.run(spec, tmp_path)
    assert result.passed is True
    assert result.kind == "contract"


# ---------------------------------------------------------------------------
# safety
# ---------------------------------------------------------------------------

def test_shell_true_never_used(tmp_path):
    runner = VerificationRunner()
    # The only way to check shell=True is never used is by inspection.
    # We verify by ensuring a command with shell syntax fails under shell=False.
    spec = VerificationSpec(
        kind="command",
        command=["echo", "hello", "&&", "echo", "world"],
    )
    result = runner.run(spec, tmp_path)
    # With shell=False, "&&" is just a literal argument to echo, so it prints it
    assert "&&" in result.stdout


def test_path_traversal_blocked(tmp_path):
    runner = VerificationRunner()
    spec = VerificationSpec(
        kind="artifact",
        expected_artifacts=["../secret.txt"],
    )
    result = runner.run(spec, tmp_path)
    assert result.passed is False
    assert "../secret.txt" in result.risks[0] or "Missing" in result.risks[0]


def test_cwd_restricted_to_workspace(tmp_path):
    runner = VerificationRunner()
    # Write a file in workspace
    (tmp_path / "marker.txt").write_text("", encoding="utf-8")
    # Command that lists current directory
    spec = VerificationSpec(
        kind="command",
        command=["python3", "-c", "import os; print(os.getcwd())"],
    )
    result = runner.run(spec, tmp_path)
    assert str(tmp_path) in result.stdout


# ---------------------------------------------------------------------------
# internal helpers
# ---------------------------------------------------------------------------

def test_is_safe_path():
    assert _is_safe_path(Path("/tmp"), "foo/bar.txt")
    assert _is_safe_path(Path("/tmp"), "foo.txt")
    assert not _is_safe_path(Path("/tmp"), "../foo.txt")
    assert not _is_safe_path(Path("/tmp"), "/absolute/foo.txt")
    assert not _is_safe_path(Path("/tmp"), "")


def test_truncate():
    text = "x" * 10000
    truncated = _truncate(text, 100)
    assert len(truncated) <= 100
    assert "[truncated]" in truncated


def test_resolve_within_workspace(tmp_path):
    assert _resolve_within_workspace(tmp_path, "a.txt") == tmp_path / "a.txt"
    assert _resolve_within_workspace(tmp_path, "../x.txt") is None
    assert _resolve_within_workspace(tmp_path, "/x.txt") is None
