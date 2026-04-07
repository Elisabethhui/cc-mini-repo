#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_manifest(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"Manifest not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid manifest JSON: {exc}") from exc


def save_manifest(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Update manifest after project-architecture run")
    parser.add_argument("--manifest", default="./code-reading-notes/manifest.json", help="Path to manifest.json")
    parser.add_argument("--status", choices=["pending", "done", "failed"], required=True, help="New project summary status")
    parser.add_argument("--arch-file", default="./code-reading-notes/30_project_summary/project_architecture.md", help="Architecture markdown path")
    parser.add_argument("--highlights-file", default="./code-reading-notes/30_project_summary/project_technical_highlights.md", help="Technical highlights markdown path")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = load_manifest(manifest_path)

    project_summary = manifest.setdefault("project_summary", {})
    project_summary["status"] = args.status
    project_summary["arch_file"] = args.arch_file
    project_summary["highlights_file"] = args.highlights_file
    project_summary["last_processed_at"] = now_iso()

    progress = manifest.setdefault("progress", {})
    progress["last_skill"] = "project-architecture"
    progress["updated_at"] = now_iso()

    save_manifest(manifest_path, manifest)

    print(json.dumps({
        "manifest": str(manifest_path),
        "status": args.status,
        "arch_file": args.arch_file,
        "highlights_file": args.highlights_file,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
