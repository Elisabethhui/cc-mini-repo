from __future__ import annotations

from core.workflow_init import (
    WORKFLOW_SCAFFOLD,
    format_workflow_init_result,
    init_workflow_scaffold,
    inspect_workflow_scaffold,
    list_missing_workflow_files,
)


def test_list_missing_workflow_files_for_empty_root(tmp_path):
    missing = list_missing_workflow_files(tmp_path)

    assert missing == tuple(item.rel_path for item in WORKFLOW_SCAFFOLD)


def test_init_workflow_scaffold_creates_missing_files(tmp_path):
    result = init_workflow_scaffold(tmp_path)

    assert result.dry_run is False
    assert result.created == tuple(item.rel_path for item in WORKFLOW_SCAFFOLD)
    assert result.skipped == ()
    assert result.conflicts == ()
    for scaffold in WORKFLOW_SCAFFOLD:
        assert (tmp_path / scaffold.rel_path).read_text(encoding="utf-8") == scaffold.content


def test_init_workflow_scaffold_dry_run_does_not_write(tmp_path):
    result = init_workflow_scaffold(tmp_path, dry_run=True)

    assert result.dry_run is True
    assert result.created == tuple(item.rel_path for item in WORKFLOW_SCAFFOLD)
    assert result.skipped == ()
    assert result.conflicts == ()
    assert not (tmp_path / ".ai-dev").exists()


def test_init_workflow_scaffold_skips_existing_files_without_overwrite(tmp_path):
    existing = tmp_path / ".ai-dev" / "README.md"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("keep me\n", encoding="utf-8")

    result = init_workflow_scaffold(tmp_path)

    assert ".ai-dev/README.md" in result.skipped
    assert ".ai-dev/README.md" not in result.created
    assert existing.read_text(encoding="utf-8") == "keep me\n"
    assert (tmp_path / ".ai-dev" / "WORKFLOW.md").exists()


def test_init_workflow_scaffold_reports_conflicts(tmp_path):
    conflict = tmp_path / ".ai-dev" / "templates"
    conflict.parent.mkdir(parents=True, exist_ok=True)
    conflict.write_text("not a directory\n", encoding="utf-8")

    inspection = inspect_workflow_scaffold(tmp_path)
    result = init_workflow_scaffold(tmp_path)

    assert ".ai-dev/templates/CURRENT_TASK.md" in inspection.conflicts
    assert ".ai-dev/templates/CURRENT_TASK.md" in result.conflicts
    assert ".ai-dev/templates/CONTEXT_PACK.md" in result.conflicts
    assert ".ai-dev/README.md" in result.created
    assert conflict.read_text(encoding="utf-8") == "not a directory\n"


def test_init_workflow_scaffold_creates_agents_md(tmp_path):
    result = init_workflow_scaffold(tmp_path)

    assert "AGENTS.md" in result.created
    assert (tmp_path / "AGENTS.md").exists()
    assert "context-bounded" in (tmp_path / "AGENTS.md").read_text(encoding="utf-8")


def test_init_workflow_scaffold_creates_skills_gitkeep(tmp_path):
    result = init_workflow_scaffold(tmp_path)

    assert ".ai-dev/skills/.gitkeep" in result.created
    assert (tmp_path / ".ai-dev" / "skills" / ".gitkeep").exists()
    assert (tmp_path / ".ai-dev" / "skills").is_dir()


def test_init_workflow_scaffold_preserves_existing_agents_md(tmp_path):
    agents = tmp_path / "AGENTS.md"
    agents.write_text("existing rules\n", encoding="utf-8")

    result = init_workflow_scaffold(tmp_path)

    assert "AGENTS.md" in result.skipped
    assert agents.read_text(encoding="utf-8") == "existing rules\n"


def test_init_workflow_scaffold_preserves_existing_skills_dir(tmp_path):
    skills_dir = tmp_path / ".ai-dev" / "skills"
    skills_dir.mkdir(parents=True)
    skills_dir.joinpath("my-skill.md").write_text("skill\n", encoding="utf-8")

    result = init_workflow_scaffold(tmp_path)

    assert ".ai-dev/skills/.gitkeep" in result.created
    assert skills_dir.joinpath("my-skill.md").read_text(encoding="utf-8") == "skill\n"
    assert skills_dir.is_dir()


def test_format_workflow_init_result_is_stable(tmp_path):
    result = init_workflow_scaffold(tmp_path, dry_run=True)

    text = format_workflow_init_result(result)

    expected = """Workflow init dry run

Created:
- AGENTS.md
- .ai-dev/README.md
- .ai-dev/WORKFLOW.md
- .ai-dev/skills/.gitkeep
- .ai-dev/templates/CURRENT_TASK.md
- .ai-dev/templates/CONTEXT_PACK.md
- .ai-dev/templates/TEST_GATE.md
- .ai-dev/templates/REVIEW_ROLLBACK.md
- .ai-dev/templates/WORK_LOG.md

Skipped:
- (none)

Conflicts:
- (none)"""
    assert text == expected
