#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_manifest(repo_root: str) -> dict:
    return {
        "repo_root": repo_root,
        "scan": {
            "done": False,
            "snapshot_file": "./code-reading-notes/00_repo_scan/repo_snapshot.json",
            "entry_candidates": [],
            "config_candidates": [],
            "module_candidates_file": "./code-reading-notes/00_repo_scan/module_candidates.json",
            "reading_order_file": "./code-reading-notes/00_repo_scan/reading_order.md",
        },
        "files": {},
        "modules": {},
        "project_summary": {
            "status": "pending",
            "arch_file": "./code-reading-notes/30_project_summary/project_architecture.md",
            "highlights_file": "./code-reading-notes/30_project_summary/project_technical_highlights.md",
        },
        "interview_notes": {
            "status": "pending",
            "files": [],
        },
        "progress": {
            "last_skill": "",
            "updated_at": now_iso(),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize code-reading manifest files")
    parser.add_argument("--repo-root", required=True, help="Absolute project root")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    notes_dir = repo_root / "code-reading-notes"
    scan_dir = notes_dir / "00_repo_scan"
    file_dir = notes_dir / "10_file_notes"
    module_dir = notes_dir / "20_module_notes"
    summary_dir = notes_dir / "30_project_summary"
    interview_dir = notes_dir / "40_interview_notes"

    for d in [notes_dir, scan_dir, file_dir, module_dir, summary_dir, interview_dir]:
        d.mkdir(parents=True, exist_ok=True)

    manifest_path = notes_dir / "manifest.json"
    todo_path = notes_dir / "TODO.md"
    progress_path = notes_dir / "progress.md"

    if not manifest_path.exists():
        manifest_path.write_text(
            json.dumps(default_manifest(str(repo_root)), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if not todo_path.exists():
        todo_path.write_text(
            "# TODO\n\n- [ ] Run /repo-scan\n- [ ] Generate file notes\n- [ ] Generate module notes\n- [ ] Generate project architecture\n- [ ] Generate interview notes\n",
            encoding="utf-8",
        )

    if not progress_path.exists():
        progress_path.write_text(
            "# Progress\n\n- Initialized code-reading-notes structure.\n",
            encoding="utf-8",
        )

    print(json.dumps({
        "repo_root": str(repo_root),
        "notes_dir": str(notes_dir),
        "manifest": str(manifest_path),
        "todo": str(todo_path),
        "progress": str(progress_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
