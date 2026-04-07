
import json
from pathlib import Path
from core.checkpoint import CheckpointManager


def test_checkpoint_manager_writes_manifest_progress_and_report(tmp_repo, monkeypatch):
    monkeypatch.chdir(tmp_repo)
    mgr = CheckpointManager(repo_root=tmp_repo)
    mgr.write_checkpoint(
        skill="repo-scan",
        reason="token_high_watermark",
        next_skill="/resume-from-checkpoint",
        artifacts_written=["a.md", "b.json"],
        token_estimate=27000,
        budget_state="checkpoint",
        dehydrated_items=3,
    )
    manifest = json.loads((tmp_repo / "code-reading-notes" / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["runtime"]["last_checkpoint_reason"] == "token_high_watermark"
    assert manifest["runtime"]["last_resume_recommendation"] == "/resume-from-checkpoint"
    assert manifest["checkpoints"][-1]["skill"] == "repo-scan"
    progress = (tmp_repo / "code-reading-notes" / "progress.md").read_text(encoding="utf-8")
    report = (tmp_repo / "code-reading-notes" / "checkpoint_report.md").read_text(encoding="utf-8")
    assert "/resume-from-checkpoint" in progress
    assert "repo-scan" in report
