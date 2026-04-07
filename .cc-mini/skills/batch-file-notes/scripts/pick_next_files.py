#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

PRIORITY_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}


def load_manifest(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Manifest not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid manifest JSON: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Pick the next unfinished important files from manifest")
    parser.add_argument("--manifest", default="./code-reading-notes/manifest.json", help="Path to manifest.json")
    parser.add_argument("--count", type=int, default=3, help="Number of files to pick (default 3, max 5)")
    parser.add_argument("--format", choices=["text", "json"], default="json")
    args = parser.parse_args()

    count = max(1, min(args.count, 5))
    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = load_manifest(manifest_path)

    files = manifest.get("files", {})
    rows = []
    for rel_path, meta in files.items():
        status = meta.get("status", "pending")
        if status == "done":
            continue
        priority = meta.get("priority", "D")
        rows.append({
            "path": rel_path,
            "priority": priority,
            "status": status,
            "module": meta.get("module"),
            "note_file": meta.get("note_file"),
        })

    rows.sort(key=lambda x: (PRIORITY_ORDER.get(x["priority"], 99), x["path"]))
    selected = rows[:count]

    if args.format == "text":
        for row in selected:
            print(row["path"])
    else:
        print(json.dumps({
            "manifest": str(manifest_path),
            "count_requested": args.count,
            "count_selected": len(selected),
            "selected_files": selected,
        }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
