from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class CheckpointRecord:
    time: str
    skill: str
    reason: str
    next_skill: str
    artifacts_written: list[str]


class CheckpointManager:
    def __init__(self, repo_root: str) -> None:
        self.repo_root = Path(repo_root).expanduser().resolve()
        self.notes_root = self.repo_root / "code-reading-notes"
        self.manifest_path = self.notes_root / "manifest.json"
        self.progress_path = self.notes_root / "progress.md"
        self.checkpoint_report_path = self.notes_root / "checkpoint_report.md"

    def write_checkpoint(
        self,
        skill: str,
        reason: str,
        next_skill: str,
        artifacts_written: list[str],
        token_estimate: int | None = None,
        budget_state: str | None = None,
        dehydrated_items: int | None = None,
    ) -> None:
        manifest = self._load_manifest()

        runtime = manifest.setdefault("runtime", {})
        runtime["last_checkpoint_at"] = now_iso()
        runtime["last_checkpoint_reason"] = reason
        runtime["last_resume_recommendation"] = next_skill
        if token_estimate is not None:
            runtime["last_token_estimate"] = token_estimate
        if budget_state is not None:
            runtime["last_budget_state"] = budget_state
        if dehydrated_items is not None:
            runtime["dehydrated_items"] = dehydrated_items

        checkpoints = manifest.setdefault("checkpoints", [])
        checkpoints.append(
            asdict(
                CheckpointRecord(
                    time=now_iso(),
                    skill=skill,
                    reason=reason,
                    next_skill=next_skill,
                    artifacts_written=artifacts_written,
                )
            )
        )

        progress = manifest.setdefault("progress", {})
        progress["last_skill"] = skill
        progress["updated_at"] = now_iso()

        self._save_manifest(manifest)
        self._write_progress(skill, reason, next_skill, artifacts_written)
        self._write_checkpoint_report(skill, reason, next_skill, artifacts_written)

    def _load_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            return {"repo_root": str(self.repo_root)}
        try:
            return json.loads(self.manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {"repo_root": str(self.repo_root)}

    def _save_manifest(self, manifest: dict[str, Any]) -> None:
        self.notes_root.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _write_progress(
        self,
        skill: str,
        reason: str,
        next_skill: str,
        artifacts_written: list[str],
    ) -> None:
        lines = [
            "# Progress",
            "",
            "## Last interruption",
            f"- skill: `{skill}`",
            f"- reason: `{reason}`",
            "",
            "## Saved artifacts",
        ]
        lines.extend(f"- `{p}`" for p in artifacts_written)
        lines.extend([
            "",
            "## Recommended next step",
            f"- `{next_skill}`",
            "",
        ])
        self.progress_path.write_text("\n".join(lines), encoding="utf-8")

    def _write_checkpoint_report(
        self,
        skill: str,
        reason: str,
        next_skill: str,
        artifacts_written: list[str],
    ) -> None:
        lines = [
            "# Checkpoint Report",
            "",
            "## Current skill",
            f"`{skill}`",
            "",
            "## Reason for checkpoint",
            f"- {reason}",
            "",
            "## Saved artifacts",
        ]
        lines.extend(f"- `{p}`" for p in artifacts_written)
        lines.extend([
            "",
            "## Recommended next step",
            f"- `{next_skill}`",
            "",
        ])
        self.checkpoint_report_path.write_text("\n".join(lines), encoding="utf-8")