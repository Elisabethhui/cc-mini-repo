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


def next_skill(manifest: dict) -> str:
    if not manifest.get("scan", {}).get("done"):
        return "/repo-scan"
    files = manifest.get("files", {})
    if files and any(meta.get("status", "pending") != "done" for meta in files.values()):
        return "/batch-file-notes 3"
    modules = manifest.get("modules", {})
    if modules and any(meta.get("status", "pending") != "done" for meta in modules.values()):
        return "/module-note <module>"
    if manifest.get("project_summary", {}).get("status") != "done":
        return "/project-architecture"
    if manifest.get("interview_notes", {}).get("status") != "done":
        return "/project-interview"
    return "All planned stages are complete."


def next_targets(manifest: dict, limit: int = 3) -> dict:
    files = []
    for path, meta in manifest.get("files", {}).items():
        if meta.get("status", "pending") != "done":
            files.append(path)
    modules = []
    for name, meta in manifest.get("modules", {}).items():
        if meta.get("status", "pending") != "done":
            modules.append(name)
    return {
        "files": files[:limit],
        "modules": modules[:limit],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Report code-reading workflow progress")
    parser.add_argument("--notes-root", default="./code-reading-notes", help="Root notes directory")
    args = parser.parse_args()

    notes_root = Path(args.notes_root).expanduser().resolve()
    manifest = load_json(notes_root / "manifest.json")

    files = manifest.get("files", {})
    modules = manifest.get("modules", {})

    file_done = sum(1 for m in files.values() if m.get("status") == "done")
    file_total = len(files)
    module_done = sum(1 for m in modules.values() if m.get("status") == "done")
    module_total = len(modules)

    report = {
        "notes_root": str(notes_root),
        "scan_done": manifest.get("scan", {}).get("done", False),
        "file_notes_done": file_done,
        "file_notes_total": file_total,
        "module_notes_done": module_done,
        "module_notes_total": module_total,
        "project_summary_status": manifest.get("project_summary", {}).get("status", "pending"),
        "interview_notes_status": manifest.get("interview_notes", {}).get("status", "pending"),
        "recommended_next_skill": next_skill(manifest),
        "next_targets": next_targets(manifest),
    }

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
