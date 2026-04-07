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
    parser = argparse.ArgumentParser(description="Update manifest after one file-note run")
    parser.add_argument("--manifest", default="./code-reading-notes/manifest.json", help="Path to manifest.json")
    parser.add_argument("--file", required=True, help="Repository-relative file path")
    parser.add_argument("--status", choices=["pending", "done", "skipped", "failed"], required=True, help="New status")
    parser.add_argument("--note-file", default="", help="Generated markdown note path")
    parser.add_argument("--module", default="", help="Optional module name to set or update")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = load_manifest(manifest_path)

    files = manifest.setdefault("files", {})
    entry = files.setdefault(args.file, {})
    entry["status"] = args.status
    if args.note_file:
        entry["note_file"] = args.note_file
    if args.module:
        entry["module"] = args.module
    entry["last_processed_at"] = now_iso()

    progress = manifest.setdefault("progress", {})
    progress["last_skill"] = "file-note"
    progress["updated_at"] = now_iso()

    save_manifest(manifest_path, manifest)

    print(json.dumps({
        "updated_file": args.file,
        "status": args.status,
        "note_file": entry.get("note_file"),
        "module": entry.get("module"),
        "manifest": str(manifest_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
