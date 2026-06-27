from __future__ import annotations

import subprocess

import pytest

from core.code_retrieval import CodeGraphRetrievalAdapter, RetrievalResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_run_factory(mapping: dict[str, object]) -> object:
    """Return a fake subprocess.run that dispatches on argv[0]."""
    def fake_run(*args, **kwargs):
        argv = tuple(args[0])
        key = argv[0]
        if key in mapping:
            return mapping[key]()
        class Default:
            returncode = 0
            stdout = ""
            stderr = ""
        return Default()
    return fake_run


# ---------------------------------------------------------------------------
# query_symbols
# ---------------------------------------------------------------------------

def test_query_symbols_uses_codegraph_when_available(monkeypatch, tmp_path):
    monkeypatch.setattr("core.code_retrieval.shutil.which", lambda name: f"/usr/bin/{name}")

    class CGResult:
        returncode = 0
        stdout = "src/core/engine.py:42:def run_query\n"
        stderr = ""

    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):
        calls.append(tuple(args[0]))
        return CGResult()

    monkeypatch.setattr("core.code_retrieval.subprocess.run", fake_run)

    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.query_symbols("run_query")

    assert result.provider == "codegraph"
    assert result.query_type == "symbols"
    assert result.ok is True
    assert result.items == ("src/core/engine.py:42:def run_query",)
    assert result.confidence == 0.95
    assert result.warnings == ()
    assert result.truncated is False
    assert calls == [("codegraph", "node", "run_query")]


def test_query_symbols_falls_back_to_rg(monkeypatch, tmp_path):
    monkeypatch.setattr("core.code_retrieval.shutil.which", lambda name: f"/usr/bin/{name}")

    class CGFailure:
        returncode = 1
        stdout = ""
        stderr = "node not found"

    class RGSuccess:
        returncode = 0
        stdout = "src/core/engine.py:42:def run_query\n"
        stderr = ""

    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):
        argv = tuple(args[0])
        calls.append(argv)
        if argv[0] == "codegraph":
            return CGFailure()
        return RGSuccess()

    monkeypatch.setattr("core.code_retrieval.subprocess.run", fake_run)

    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.query_symbols("run_query")

    assert result.provider == "rg"
    assert result.ok is True
    assert result.items == ("src/core/engine.py:42:def run_query",)
    assert result.confidence == 0.65
    assert "codegraph query failed; using rg fallback" in result.warnings
    assert len(calls) == 2


def test_query_symbols_empty_rejected(tmp_path):
    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.query_symbols("   ")

    assert result.provider == "none"
    assert result.ok is False
    assert result.confidence == 0.0
    assert result.warnings == ("symbol query is empty",)


# ---------------------------------------------------------------------------
# query_files
# ---------------------------------------------------------------------------

def test_query_files_uses_codegraph(monkeypatch, tmp_path):
    monkeypatch.setattr("core.code_retrieval.shutil.which", lambda name: f"/usr/bin/{name}")

    class CGResult:
        returncode = 0
        stdout = "src/core/engine.py\nsrc/core/config.py\n"
        stderr = ""

    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):
        calls.append(tuple(args[0]))
        return CGResult()

    monkeypatch.setattr("core.code_retrieval.subprocess.run", fake_run)

    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.query_files("engine")

    assert result.provider == "codegraph"
    assert result.query_type == "files"
    assert result.ok is True
    assert "src/core/engine.py" in result.items
    assert result.confidence == 0.95
    assert calls == [("codegraph", "files", "engine")]


# ---------------------------------------------------------------------------
# query_tests
# ---------------------------------------------------------------------------

def test_query_tests_uses_codegraph(monkeypatch, tmp_path):
    monkeypatch.setattr("core.code_retrieval.shutil.which", lambda name: f"/usr/bin/{name}")

    class CGResult:
        returncode = 0
        stdout = "tests/test_engine.py:10:def test_run_query\n"
        stderr = ""

    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):
        calls.append(tuple(args[0]))
        return CGResult()

    monkeypatch.setattr("core.code_retrieval.subprocess.run", fake_run)

    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.query_tests("run_query")

    assert result.provider == "codegraph"
    assert result.query_type == "tests"
    assert result.ok is True
    assert result.items == ("tests/test_engine.py:10:def test_run_query",)
    assert result.confidence == 0.95
    assert calls == [("codegraph", "test", "run_query")]


# ---------------------------------------------------------------------------
# query_callers
# ---------------------------------------------------------------------------

def test_query_callers_uses_codegraph(monkeypatch, tmp_path):
    monkeypatch.setattr("core.code_retrieval.shutil.which", lambda name: f"/usr/bin/{name}")

    class CGResult:
        returncode = 0
        stdout = "src/core/main.py:30:run_query(engine, prompt)\n"
        stderr = ""

    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):
        calls.append(tuple(args[0]))
        return CGResult()

    monkeypatch.setattr("core.code_retrieval.subprocess.run", fake_run)

    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.query_callers("run_query")

    assert result.provider == "codegraph"
    assert result.query_type == "callers"
    assert result.ok is True
    assert result.items == ("src/core/main.py:30:run_query(engine, prompt)",)
    assert result.confidence == 0.95
    assert calls == [("codegraph", "callers", "run_query")]


# ---------------------------------------------------------------------------
# query_impact
# ---------------------------------------------------------------------------

def test_query_impact_uses_codegraph(monkeypatch, tmp_path):
    monkeypatch.setattr("core.code_retrieval.shutil.which", lambda name: f"/usr/bin/{name}")

    class CGResult:
        returncode = 0
        stdout = "src/core/engine.py\nsrc/core/main.py\n"
        stderr = ""

    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):
        calls.append(tuple(args[0]))
        return CGResult()

    monkeypatch.setattr("core.code_retrieval.subprocess.run", fake_run)

    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.query_impact("engine.py")

    assert result.provider == "codegraph"
    assert result.query_type == "impact"
    assert result.ok is True
    assert "src/core/engine.py" in result.items
    assert result.confidence == 0.95
    assert calls == [("codegraph", "impact", "engine.py")]


# ---------------------------------------------------------------------------
# fallback_rg
# ---------------------------------------------------------------------------

def test_fallback_rg_skips_codegraph(monkeypatch, tmp_path):
    monkeypatch.setattr("core.code_retrieval.shutil.which", lambda name: f"/usr/bin/{name}")

    class RGResult:
        returncode = 0
        stdout = "src/core/engine.py:1:import os\n"
        stderr = ""

    calls: list[tuple[str, ...]] = []

    def fake_run(*args, **kwargs):
        calls.append(tuple(args[0]))
        return RGResult()

    monkeypatch.setattr("core.code_retrieval.subprocess.run", fake_run)

    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.fallback_rg("import os")

    assert result.provider == "rg"
    assert result.query_type == "fallback_rg"
    assert result.ok is True
    assert result.confidence == 0.65
    assert len(calls) == 1
    assert calls[0][0] == "rg"


def test_fallback_rg_empty_rejected(tmp_path):
    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.fallback_rg("   ")

    assert result.provider == "none"
    assert result.ok is False
    assert result.confidence == 0.0
    assert result.warnings == ("fallback query is empty",)


# ---------------------------------------------------------------------------
# Confidence and truncation
# ---------------------------------------------------------------------------

def test_confidence_codegraph_full(monkeypatch, tmp_path):
    monkeypatch.setattr("core.code_retrieval.shutil.which", lambda name: f"/usr/bin/{name}")

    class CGResult:
        returncode = 0
        stdout = "one\n"
        stderr = ""

    monkeypatch.setattr("core.code_retrieval.subprocess.run", lambda *a, **k: CGResult())

    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.query_symbols("x")
    assert result.confidence == 0.95
    assert result.truncated is False


def test_confidence_codegraph_truncated(monkeypatch, tmp_path):
    monkeypatch.setattr("core.code_retrieval.shutil.which", lambda name: f"/usr/bin/{name}")

    class CGResult:
        returncode = 0
        stdout = "line-0\nline-1\nline-2\n"
        stderr = ""

    monkeypatch.setattr("core.code_retrieval.subprocess.run", lambda *a, **k: CGResult())

    adapter = CodeGraphRetrievalAdapter(tmp_path, max_items=1, max_lines=2)
    result = adapter.query_symbols("x")
    assert result.confidence == 0.85
    assert result.truncated is True


def test_confidence_rg_full(monkeypatch, tmp_path):
    monkeypatch.setattr("core.code_retrieval.shutil.which", lambda name: "/usr/bin/rg" if name == "rg" else None)

    class RGResult:
        returncode = 0
        stdout = "one\n"
        stderr = ""

    monkeypatch.setattr("core.code_retrieval.subprocess.run", lambda *a, **k: RGResult())

    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.query_symbols("x")
    assert result.provider == "rg"
    assert result.confidence == 0.65
    assert result.truncated is False


def test_confidence_rg_truncated(monkeypatch, tmp_path):
    monkeypatch.setattr("core.code_retrieval.shutil.which", lambda name: "/usr/bin/rg" if name == "rg" else None)

    class RGResult:
        returncode = 0
        stdout = "line-0\nline-1\nline-2\n"
        stderr = ""

    monkeypatch.setattr("core.code_retrieval.subprocess.run", lambda *a, **k: RGResult())

    adapter = CodeGraphRetrievalAdapter(tmp_path, max_items=1, max_lines=2)
    result = adapter.query_symbols("x")
    assert result.provider == "rg"
    assert result.confidence == 0.55
    assert result.truncated is True


# ---------------------------------------------------------------------------
# Nonfatal fallback when codegraph unavailable
# ---------------------------------------------------------------------------

def test_codegraph_unavailable_nonfatal(monkeypatch, tmp_path):
    monkeypatch.setattr("core.code_retrieval.shutil.which", lambda name: "/usr/bin/rg" if name == "rg" else None)

    class RGResult:
        returncode = 0
        stdout = "found\n"
        stderr = ""

    monkeypatch.setattr("core.code_retrieval.subprocess.run", lambda *a, **k: RGResult())

    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = adapter.query_symbols("symbol")

    assert result.provider == "rg"
    assert result.ok is True
    assert result.items == ("found",)
    assert "codegraph not available; using rg fallback" in result.warnings


def test_initialized_detects_codegraph_dir(tmp_path):
    adapter = CodeGraphRetrievalAdapter(tmp_path)
    assert adapter.initialized() is False

    (tmp_path / ".codegraph").mkdir()
    assert adapter.initialized() is True


# ---------------------------------------------------------------------------
# All query types reject empty input
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("method,expected_type", [
    ("query_symbols", "symbols"),
    ("query_files", "files"),
    ("query_tests", "tests"),
    ("query_callers", "callers"),
    ("query_impact", "impact"),
])
def test_all_methods_reject_empty_input(tmp_path, method, expected_type):
    adapter = CodeGraphRetrievalAdapter(tmp_path)
    result = getattr(adapter, method)("   ")
    assert result.provider == "none"
    assert result.query_type == expected_type
    assert result.ok is False
    assert result.confidence == 0.0
