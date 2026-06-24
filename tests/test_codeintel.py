from __future__ import annotations

import subprocess

from core.codeintel import CodeIntelProvider


def test_available_detects_codegraph(monkeypatch, tmp_path):
    monkeypatch.setattr("core.codeintel.shutil.which", lambda name: f"/usr/bin/{name}" if name == "codegraph" else None)

    provider = CodeIntelProvider(tmp_path)

    assert provider.available() is True


def test_status_uses_codegraph_when_available(monkeypatch, tmp_path):
    monkeypatch.setattr("core.codeintel.shutil.which", lambda name: f"/usr/bin/{name}")

    class Result:
        returncode = 0
        stdout = "index: ready\nfiles: 10\n"
        stderr = ""

    calls: list[tuple[object, ...]] = []

    def fake_run(*args, **kwargs):
        calls.append(tuple(kwargs["args"]) if "args" in kwargs else tuple(args[0]))
        assert kwargs["timeout"] == 2.0
        return Result()

    monkeypatch.setattr("core.codeintel.subprocess.run", fake_run)

    provider = CodeIntelProvider(tmp_path)
    result = provider.status()

    assert result.provider == "codegraph"
    assert result.ok is True
    assert result.items == ("index: ready", "files: 10")
    assert result.warnings == ()
    assert result.truncated is False
    assert calls == [("codegraph", "status")]


def test_query_falls_back_to_rg_when_codegraph_missing(monkeypatch, tmp_path):
    monkeypatch.setattr("core.codeintel.shutil.which", lambda name: "/usr/bin/rg" if name == "rg" else None)

    class Result:
        returncode = 0
        stdout = "./src/core/workflow_doctor.py:10:DoctorCheck\n"
        stderr = ""

    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):
        calls.append(tuple(args[0]))
        return Result()

    monkeypatch.setattr("core.codeintel.subprocess.run", fake_run)

    provider = CodeIntelProvider(tmp_path)
    result = provider.query("DoctorCheck")

    assert result.provider == "rg"
    assert result.ok is True
    assert result.items == ("./src/core/workflow_doctor.py:10:DoctorCheck",)
    assert "codegraph not available; using rg fallback" in result.warnings
    assert calls == [("rg", "-n", "--no-heading", "--color", "never", "DoctorCheck", ".")]


def test_query_falls_back_to_rg_after_codegraph_error(monkeypatch, tmp_path):
    monkeypatch.setattr("core.codeintel.shutil.which", lambda name: f"/usr/bin/{name}")

    class Failure:
        returncode = 1
        stdout = ""
        stderr = "query failed"

    class Success:
        returncode = 0
        stdout = "./src/core/codeintel.py:1:from __future__ import annotations\n"
        stderr = ""

    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):
        argv = tuple(args[0])
        calls.append(argv)
        if argv[0] == "codegraph":
            return Failure()
        return Success()

    monkeypatch.setattr("core.codeintel.subprocess.run", fake_run)

    provider = CodeIntelProvider(tmp_path)
    result = provider.query("annotations")

    assert result.provider == "rg"
    assert result.ok is True
    assert result.items == ("./src/core/codeintel.py:1:from __future__ import annotations",)
    assert "query failed" in result.warnings
    assert "codegraph query failed; using rg fallback" in result.warnings
    assert calls == [
        ("codegraph", "query", "annotations"),
        ("rg", "-n", "--no-heading", "--color", "never", "annotations", "."),
    ]


def test_query_handles_timeout_and_returns_empty_when_rg_unavailable(monkeypatch, tmp_path):
    monkeypatch.setattr("core.codeintel.shutil.which", lambda name: "/usr/bin/codegraph" if name == "codegraph" else None)

    def fake_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd=args[0], timeout=kwargs["timeout"])

    monkeypatch.setattr("core.codeintel.subprocess.run", fake_run)

    provider = CodeIntelProvider(tmp_path)
    result = provider.query("symbol")

    assert result.provider == "rg"
    assert result.ok is False
    assert result.items == ()
    assert f"codegraph timed out after {provider.timeout_seconds:g}s" in result.warnings
    assert "codegraph query failed; using rg fallback" in result.warnings
    assert "rg not available" in result.warnings


def test_status_falls_back_to_rg_and_truncates_output(monkeypatch, tmp_path):
    monkeypatch.setattr("core.codeintel.shutil.which", lambda name: f"/usr/bin/{name}")

    class Failure:
        returncode = 2
        stdout = ""
        stderr = "status unavailable"

    class Success:
        returncode = 0
        stdout = "\n".join(f"line-{index}" for index in range(10))
        stderr = ""

    def fake_run(*args, **kwargs):
        argv = tuple(args[0])
        if argv[0] == "codegraph":
            return Failure()
        return Success()

    monkeypatch.setattr("core.codeintel.subprocess.run", fake_run)

    provider = CodeIntelProvider(tmp_path, max_items=3, max_lines=5, max_chars=18)
    result = provider.status()

    assert result.provider == "rg"
    assert result.ok is True
    assert result.items == ("line-0", "line-1")
    assert result.truncated is True
    assert "status unavailable" in result.warnings
    assert "codegraph status failed; using rg fallback" in result.warnings


def test_query_rejects_empty_keyword(tmp_path):
    provider = CodeIntelProvider(tmp_path)

    result = provider.query("   ")

    assert result.provider == "none"
    assert result.ok is False
    assert result.items == ()
    assert result.warnings == ("query is empty",)
