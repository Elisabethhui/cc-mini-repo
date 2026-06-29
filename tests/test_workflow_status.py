from __future__ import annotations

from pathlib import Path

from core.workflow_status import collect_workflow_status, format_workflow_status


def _make_workflow_tree(root: Path) -> None:
    (root / "AGENTS.md").write_text("rules\n", encoding="utf-8")
    (root / ".ai-dev" / "README.md").parent.mkdir(parents=True, exist_ok=True)
    (root / ".ai-dev" / "README.md").write_text("readme\n", encoding="utf-8")
    (root / ".ai-dev" / "WORKFLOW.md").write_text("workflow\n", encoding="utf-8")
    (root / ".ai-dev" / "skills").mkdir()
    (root / ".ai-dev" / "templates").mkdir()
    (root / ".ai-dev" / "tasks").mkdir()
    (root / ".ai-dev" / "context-packs").mkdir()
    (root / ".ai-dev" / "worklogs").mkdir()
    (root / ".ai-dev" / "checkpoints").mkdir()
    (root / ".ai-dev" / "tmp").mkdir()
    (root / ".codegraph").mkdir()
    (root / ".codebase-memory").mkdir()


def test_collect_workflow_status_happy_path(monkeypatch, tmp_path):
    _make_workflow_tree(tmp_path)

    monkeypatch.setattr("core.workflow_status.shutil.which", lambda name: f"/usr/bin/{name}")

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr("core.workflow_status.subprocess.run", lambda *args, **kwargs: Result())

    status = collect_workflow_status(tmp_path)

    assert status.ok is True
    assert all(item.ok for item in status.required_files)
    assert all(item.ok for item in status.ignored_paths)
    assert all(item.ok for item in status.codegraph)
    assert all(item.ok for item in status.git)
    assert status.warnings == ()


def test_collect_workflow_status_reports_missing_paths(monkeypatch, tmp_path):
    (tmp_path / "AGENTS.md").write_text("rules\n", encoding="utf-8")
    monkeypatch.setattr("core.workflow_status.shutil.which", lambda name: None if name == "codegraph" else f"/usr/bin/{name}")

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr("core.workflow_status.subprocess.run", lambda *args, **kwargs: Result())

    status = collect_workflow_status(tmp_path)

    assert status.ok is False
    assert any(not item.ok and item.name == ".ai-dev/README.md" for item in status.required_files)
    # CodeGraph is optional and should not hard-fail
    assert any(item.ok and item.name == "codegraph command" for item in status.codegraph)
    assert any(item.ok and item.name == ".codegraph/" for item in status.codegraph)


def test_collect_workflow_status_warns_for_local_artifacts(monkeypatch, tmp_path):
    _make_workflow_tree(tmp_path)
    monkeypatch.setattr("core.workflow_status.shutil.which", lambda name: f"/usr/bin/{name}")

    class Result:
        returncode = 0
        stdout = "?? .ai-dev/tmp/state.md\n M pkg/__pycache__/mod.cpython-311.pyc\n"
        stderr = ""

    monkeypatch.setattr("core.workflow_status.subprocess.run", lambda *args, **kwargs: Result())

    status = collect_workflow_status(tmp_path)

    assert status.ok is False
    assert any("local workflow artifact" in warning for warning in status.warnings)
    assert any("cache artifact" in warning for warning in status.warnings)
    assert status.git_summary is not None
    assert status.git_summary.clean is False


def test_collect_workflow_status_handles_git_unavailable(monkeypatch, tmp_path):
    _make_workflow_tree(tmp_path)

    def fake_which(name: str):
        return None if name == "git" else f"/usr/bin/{name}"

    monkeypatch.setattr("core.workflow_status.shutil.which", fake_which)

    status = collect_workflow_status(tmp_path)

    # Git absence is optional and should not make status fail by itself
    assert status.git_summary is not None
    assert status.git_summary.available is False
    assert status.git[0].ok is True
    assert "optional" in status.git[0].detail


def test_format_workflow_status_is_stable(monkeypatch, tmp_path):
    _make_workflow_tree(tmp_path)
    monkeypatch.setattr("core.workflow_status.shutil.which", lambda name: f"/usr/bin/{name}")

    class Result:
        returncode = 0
        stdout = "?? .ai-dev/tmp/state.md\n"
        stderr = ""

    monkeypatch.setattr("core.workflow_status.subprocess.run", lambda *args, **kwargs: Result())

    status = collect_workflow_status(tmp_path)
    text = format_workflow_status(status)

    assert "Workflow status: NEEDS ATTENTION" in text
    assert "Required Files:" in text
    assert "Ignored Local Paths:" in text
    assert "CodeGraph:" in text
    assert "Git:" in text
    assert "Warnings:" in text
    assert ".ai-dev/tmp/state.md" in text


def test_workflow_status_required_files_pass_after_init(monkeypatch, tmp_path):
    from core.workflow_init import init_workflow_scaffold

    init_workflow_scaffold(tmp_path)

    monkeypatch.setattr("core.workflow_status.shutil.which", lambda name: f"/usr/bin/{name}")

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr("core.workflow_status.subprocess.run", lambda *args, **kwargs: Result())

    status = collect_workflow_status(tmp_path)

    assert all(item.ok for item in status.required_files)


def test_workflow_status_codegraph_optional(monkeypatch, tmp_path):
    from core.workflow_init import init_workflow_scaffold

    init_workflow_scaffold(tmp_path)

    monkeypatch.setattr("core.workflow_status.shutil.which", lambda name: None if name == "codegraph" else f"/usr/bin/{name}")

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr("core.workflow_status.subprocess.run", lambda *args, **kwargs: Result())

    status = collect_workflow_status(tmp_path)

    codegraph_checks = {item.name: item for item in status.codegraph}
    assert codegraph_checks["codegraph command"].ok is True
    assert "optional" in codegraph_checks["codegraph command"].detail
    assert codegraph_checks[".codegraph/"].ok is True
    assert "optional" in codegraph_checks[".codegraph/"].detail


def test_workflow_status_non_git_directory_does_not_crash(monkeypatch, tmp_path):
    from core.workflow_init import init_workflow_scaffold

    init_workflow_scaffold(tmp_path)

    monkeypatch.setattr("core.workflow_status.shutil.which", lambda name: None if name == "git" else f"/usr/bin/{name}")

    status = collect_workflow_status(tmp_path)

    git_checks = {item.name: item for item in status.git}
    assert git_checks["git status"].ok is True
    assert "optional" in git_checks["git status"].detail
