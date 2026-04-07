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


def parse_files(raw: str) -> list[str]:
    if not raw.strip():
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Update manifest after project-interview run")
    parser.add_argument("--manifest", default="./code-reading-notes/manifest.json", help="Path to manifest.json")
    parser.add_argument("--status", choices=["pending", "done", "failed"], required=True, help="New interview notes status")
    parser.add_argument("--files", default="", help="Comma-separated interview output files")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = load_manifest(manifest_path)

    interview_notes = manifest.setdefault("interview_notes", {})
    interview_notes["status"] = args.status
    interview_notes["files"] = parse_files(args.files)
    interview_notes["last_processed_at"] = now_iso()

    progress = manifest.setdefault("progress", {})
    progress["last_skill"] = "project-interview"
    progress["updated_at"] = now_iso()

    save_manifest(manifest_path, manifest)

    print(json.dumps({
        "manifest": str(manifest_path),
        "status": args.status,
        "files": interview_notes["files"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
