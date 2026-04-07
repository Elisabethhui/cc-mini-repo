#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Suggest the next safest skill after interruption or partial completion")
    parser.add_argument("--notes-root", default="./code-reading-notes", help="Root notes directory")
    args = parser.parse_args()

    notes_root = Path(args.notes_root).expanduser().resolve()
    manifest = load_json(notes_root / "manifest.json")

    repo_snapshot = (notes_root / "00_repo_scan" / "repo_snapshot.json").exists()
    repo_overview = (notes_root / "00_repo_scan" / "repo_overview.md").exists()
    file_notes = len(list((notes_root / "10_file_notes").glob("*.md"))) if (notes_root / "10_file_notes").exists() else 0
    module_notes = len(list((notes_root / "20_module_notes").glob("*.md"))) if (notes_root / "20_module_notes").exists() else 0
    arch_ok = (notes_root / "30_project_summary" / "project_architecture.md").exists()
    highlights_ok = (notes_root / "30_project_summary" / "project_technical_highlights.md").exists()
    interview_ok = len(list((notes_root / "40_interview_notes").glob("*.md"))) > 0 if (notes_root / "40_interview_notes").exists() else False

    recommendation = {}
    if not notes_root.exists():
        recommendation = {
            "next_skill": "/repo-bootstrap",
            "reason": "code-reading-notes directory does not exist"
        }
    elif not repo_snapshot:
        recommendation = {
            "next_skill": "/repo-bootstrap",
            "reason": "bootstrap artifacts are missing"
        }
    elif not repo_overview:
        recommendation = {
            "next_skill": "/repo-scan",
            "reason": "repo overview has not been written yet"
        }
    elif file_notes == 0:
        recommendation = {
            "next_skill": "/batch-file-notes 2",
            "reason": "no file notes exist yet"
        }
    elif module_notes == 0:
        recommendation = {
            "next_skill": "/module-note",
            "reason": "file notes exist but no module notes exist"
        }
    elif not (arch_ok and highlights_ok):
        recommendation = {
            "next_skill": "/project-architecture",
            "reason": "project summary is incomplete"
        }
    elif not interview_ok:
        recommendation = {
            "next_skill": "/project-interview",
            "reason": "interview artifacts are missing"
        }
    else:
        recommendation = {
            "next_skill": "/resume-notes",
            "reason": "all main stages appear complete"
        }

    result = {
        "repo_root": manifest.get("repo_root"),
        "repo_snapshot_exists": repo_snapshot,
        "repo_overview_exists": repo_overview,
        "file_note_count": file_notes,
        "module_note_count": module_notes,
        "project_summary_complete": arch_ok and highlights_ok,
        "interview_exists": interview_ok,
        "recommendation": recommendation,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
