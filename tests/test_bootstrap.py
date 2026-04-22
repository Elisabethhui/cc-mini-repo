from pathlib import Path

from core.bootstrap import (
    BootstrapStatus,
    bootstrap_workspace,
    doctor_workspace,
    ensure_phase1_workspace,
    inspect_phase1_workspace,
)


def test_inspect_phase1_workspace_reports_missing_for_empty_workspace(tmp_path: Path):
    result = doctor_workspace(tmp_path)

    assert result.status == BootstrapStatus.MISSING
    assert result.cc_mini_dir == tmp_path / ".cc-mini"
    assert result.wiki_dir == tmp_path / ".cc-mini" / "wiki"
    assert result.index_file == tmp_path / ".cc-mini" / "wiki" / "index.md"


def test_inspect_phase1_workspace_reports_stale_for_partial_scaffold(tmp_path: Path):
    (tmp_path / ".cc-mini").mkdir()
    (tmp_path / ".cc-mini" / "wiki").mkdir()

    result = inspect_phase1_workspace(tmp_path)

    assert result.status == BootstrapStatus.STALE
    assert tmp_path / ".cc-mini" / "wiki" / "index.md" in result.missing_paths
    assert tmp_path / ".cc-mini" / "wiki" / "entities" in result.stale_paths


def test_ensure_phase1_workspace_creates_minimal_scaffold_and_is_idempotent(tmp_path: Path):
    result = bootstrap_workspace(tmp_path)

    assert result.status == BootstrapStatus.INITIALIZED
    assert result.ready
    assert result.is_ready
    assert (tmp_path / ".cc-mini").is_dir()
    assert (tmp_path / ".cc-mini" / "wiki").is_dir()
    assert (tmp_path / ".cc-mini" / "wiki" / "entities").is_dir()
    assert (tmp_path / ".cc-mini" / "wiki" / "taskpacks").is_dir()
    assert (tmp_path / ".cc-mini" / "wiki" / "reports").is_dir()
    assert (tmp_path / ".cc-mini" / "wiki" / "index.md").exists()

    index_file = tmp_path / ".cc-mini" / "wiki" / "index.md"
    index_file.write_text("custom content", encoding="utf-8")

    second = ensure_phase1_workspace(tmp_path)

    assert second.status == BootstrapStatus.INITIALIZED
    assert index_file.read_text(encoding="utf-8") == "custom content"
    assert index_file not in second.created_paths
