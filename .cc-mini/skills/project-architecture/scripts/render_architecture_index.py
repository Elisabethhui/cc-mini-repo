#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def collect_md_names(root: Path) -> list[str]:
    if not root.exists():
        return []
    return [str(p.name) for p in sorted(root.rglob("*.md"))]


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Render an architecture index for generated project summary artifacts")
    parser.add_argument("--notes-root", default="./code-reading-notes", help="Root notes directory")
    parser.add_argument("--output", default="./code-reading-notes/30_project_summary/architecture_index.md", help="Output markdown path")
    args = parser.parse_args()

    notes_root = Path(args.notes_root).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = load_json(notes_root / "manifest.json")
    repo_scan_docs = collect_md_names(notes_root / "00_repo_scan")
    file_notes = collect_md_names(notes_root / "10_file_notes")
    module_notes = collect_md_names(notes_root / "20_module_notes")
    project_docs = collect_md_names(notes_root / "30_project_summary")

    lines = [
        "# Architecture Index",
        "",
        "## Current status",
        f"- scan: `{manifest.get('scan', {}).get('done', False)}`",
        f"- project summary status: `{manifest.get('project_summary', {}).get('status', 'pending')}`",
        "",
        "## Repo scan artifacts",
    ]
    lines += [f"- `{name}`" for name in repo_scan_docs] or ["- None"]

    lines += ["", "## File notes"]
    lines += [f"- `{name}`" for name in file_notes] or ["- None"]

    lines += ["", "## Module notes"]
    lines += [f"- `{name}`" for name in module_notes] or ["- None"]

    lines += ["", "## Project summary docs"]
    lines += [f"- `{name}`" for name in project_docs] or ["- None"]

    lines += ["", "## Suggested reading path"]
    suggested = [
        "1. Read repo_overview.md and reading_order.md",
        "2. Read the first 3~5 highest-priority file notes",
        "3. Read module notes for core_runtime, config, and agents if present",
        "4. Read project_architecture.md",
        "5. Read project_technical_highlights.md",
    ]
    lines += [f"- {x}" for x in suggested]

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output_path),
        "repo_scan_docs": len(repo_scan_docs),
        "file_notes": len(file_notes),
        "module_notes": len(module_notes),
        "project_docs": len(project_docs),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
