from __future__ import annotations

from pathlib import Path

from core.workflow_doctor import (
    collect_workflow_doctor_report,
    format_workflow_doctor_report,
)


def _make_workflow_tree(root: Path) -> None:
    (root / "AGENTS.md").write_text("rules\n", encoding="utf-8")
    (root / ".ai-dev" / "README.md").parent.mkdir(parents=True, exist_ok=True)
    (root / ".ai-dev" / "README.md").write_text("readme\n", encoding="utf-8")
    (root / ".ai-dev" / "WORKFLOW.md").write_text("workflow\n", encoding="utf-8")
    (root / ".ai-dev" / "skills").mkdir()
    (root / ".ai-dev" / "templates").mkdir()
    (root / ".ai-dev" / "templates" / "CURRENT_TASK.md").write_text("# Task\n", encoding="utf-8")
    (root / ".ai-dev" / "tasks").mkdir()
    (root / ".ai-dev" / "context-packs").mkdir()
    (root / ".ai-dev" / "worklogs").mkdir()
    (root / ".ai-dev" / "checkpoints").mkdir()
    (root / ".ai-dev" / "tmp").mkdir()
    (root / ".codegraph").mkdir()
    (root / ".codebase-memory").mkdir()


def test_collect_workflow_doctor_report_happy_path(monkeypatch, tmp_path):
    _make_workflow_tree(tmp_path)
    monkeypatch.setattr("core.workflow_doctor.shutil.which", lambda name: f"/usr/bin/{name}")

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr("core.workflow_doctor.subprocess.run", lambda *args, **kwargs: Result())

    report = collect_workflow_doctor_report(tmp_path)

    assert report.ok is True
    assert report.decision == "ok"
    assert all(check.severity == "ok" for check in report.required_files)
    assert report.local_artifacts == (report.local_artifacts[0],)
    assert report.local_artifacts[0].severity == "ok"
    assert all(check.severity == "ok" for check in report.markdown)
    assert all(check.severity == "ok" for check in report.codegraph)


def test_collect_workflow_doctor_report_fails_for_missing_required_files(monkeypatch, tmp_path):
    (tmp_path / "AGENTS.md").write_text("rules\n", encoding="utf-8")
    monkeypatch.setattr("core.workflow_doctor.shutil.which", lambda name: f"/usr/bin/{name}")

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr("core.workflow_doctor.subprocess.run", lambda *args, **kwargs: Result())

    report = collect_workflow_doctor_report(tmp_path)

    assert report.decision == "fail"
    assert any(check.name == ".ai-dev/README.md" and check.severity == "fail" for check in report.required_files)


def test_collect_workflow_doctor_report_blocks_staged_local_artifacts(monkeypatch, tmp_path):
    _make_workflow_tree(tmp_path)
    monkeypatch.setattr("core.workflow_doctor.shutil.which", lambda name: f"/usr/bin/{name}")

    class Result:
        returncode = 0
        stdout = "A  .ai-dev/tmp/state.md\n"
        stderr = ""

    monkeypatch.setattr("core.workflow_doctor.subprocess.run", lambda *args, **kwargs: Result())

    report = collect_workflow_doctor_report(tmp_path)

    assert report.decision == "blocked"
    assert any(check.name == ".ai-dev/tmp/state.md" and check.severity == "blocked" for check in report.local_artifacts)


def test_collect_workflow_doctor_report_fails_for_unclosed_markdown_fence(monkeypatch, tmp_path):
    _make_workflow_tree(tmp_path)
    (tmp_path / ".ai-dev" / "templates" / "CURRENT_TASK.md").write_text("```md\nbroken\n", encoding="utf-8")
    monkeypatch.setattr("core.workflow_doctor.shutil.which", lambda name: f"/usr/bin/{name}")

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr("core.workflow_doctor.subprocess.run", lambda *args, **kwargs: Result())

    report = collect_workflow_doctor_report(tmp_path)

    assert report.decision == "fail"
    assert any(check.name == ".ai-dev/templates/CURRENT_TASK.md" and check.severity == "fail" for check in report.markdown)


def test_collect_workflow_doctor_report_warns_when_codegraph_unavailable(monkeypatch, tmp_path):
    _make_workflow_tree(tmp_path)
    monkeypatch.setattr("core.workflow_doctor.shutil.which", lambda name: None if name == "codegraph" else f"/usr/bin/{name}")

    class Result:
        returncode = 0
        stdout = ""
        stderr = ""

    monkeypatch.setattr("core.workflow_doctor.subprocess.run", lambda *args, **kwargs: Result())

    report = collect_workflow_doctor_report(tmp_path)

    assert report.decision == "warn"
    assert any(check.name == "codegraph command" and check.severity == "warn" for check in report.codegraph)


def test_format_workflow_doctor_report_is_stable(monkeypatch, tmp_path):
    _make_workflow_tree(tmp_path)

    def fake_which(name: str):
        return None if name == "codegraph" else f"/usr/bin/{name}"

    monkeypatch.setattr("core.workflow_doctor.shutil.which", fake_which)

    class Result:
        returncode = 0
        stdout = " M .ai-dev/tmp/state.md\n"
        stderr = ""

    monkeypatch.setattr("core.workflow_doctor.subprocess.run", lambda *args, **kwargs: Result())

    report = collect_workflow_doctor_report(tmp_path)
    text = format_workflow_doctor_report(report)

    assert "Context-Bounded Workflow Doctor" in text
    assert "Required Files:" in text
    assert "Local Artifacts:" in text
    assert "Markdown:" in text
    assert "CodeGraph:" in text
    assert "- [FAIL] .ai-dev/tmp/state.md (local workflow artifact tracked by git)" in text
    assert "- [WARN] codegraph command (not installed)" in text
    assert "Decision: fail" in text
