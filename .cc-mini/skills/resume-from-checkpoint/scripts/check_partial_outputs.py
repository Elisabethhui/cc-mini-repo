#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


EXPECTED = {
    "repo_scan": [
        "00_repo_scan/repo_snapshot.json",
        "00_repo_scan/file_manifest.json",
        "00_repo_scan/module_candidates.json",
        "00_repo_scan/reading_order.md",
        "manifest.json",
        "TODO.md",
        "progress.md",
    ],
    "repo_overview": [
        "00_repo_scan/repo_overview.md",
    ],
    "project_summary": [
        "30_project_summary/project_architecture.md",
        "30_project_summary/project_technical_highlights.md",
    ],
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check existing code-reading artifacts and detect partial progress")
    parser.add_argument("--notes-root", default="./code-reading-notes", help="Root notes directory")
    parser.add_argument("--output", default="", help="Optional JSON output path")
    args = parser.parse_args()

    notes_root = Path(args.notes_root).expanduser().resolve()
    result = {
        "notes_root": str(notes_root),
        "exists": notes_root.exists(),
        "groups": {},
        "counts": {},
        "dirs": {},
    }

    subdirs = [
        "00_repo_scan",
        "10_file_notes",
        "20_module_notes",
        "30_project_summary",
        "40_interview_notes",
    ]
    for sub in subdirs:
        d = notes_root / sub
        result["dirs"][sub] = {
            "exists": d.exists(),
            "md_files": len(list(d.glob("*.md"))) if d.exists() else 0,
            "json_files": len(list(d.glob("*.json"))) if d.exists() else 0,
        }

    for group, rels in EXPECTED.items():
        rows = []
        for rel in rels:
            path = notes_root / rel
            rows.append({"path": rel, "exists": path.exists()})
        result["groups"][group] = rows
        result["counts"][group] = sum(1 for r in rows if r["exists"])

    if args.output:
        out = Path(args.output).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
