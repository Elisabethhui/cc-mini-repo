#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def collect_md(root: Path) -> list[dict]:
    rows = []
    if not root.exists():
        return rows
    for p in sorted(root.rglob("*.md")):
        rows.append({
            "path": str(p),
            "name": p.name,
            "content": p.read_text(encoding="utf-8", errors="replace"),
        })
    return rows


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect compact inputs for project interview generation")
    parser.add_argument("--notes-root", default="./code-reading-notes", help="Root notes directory")
    parser.add_argument("--output", default="./code-reading-notes/40_interview_notes/interview_inputs.json", help="Output JSON path")
    args = parser.parse_args()

    notes_root = Path(args.notes_root).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    payload = {
        "project_summary": collect_md(notes_root / "30_project_summary"),
        "module_notes": collect_md(notes_root / "20_module_notes"),
        "manifest": load_json(notes_root / "manifest.json"),
    }

    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "output": str(output_path),
        "project_summary_docs": len(payload["project_summary"]),
        "module_notes": len(payload["module_notes"]),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
