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


def parse_completed(raw: str) -> list[str]:
    if not raw.strip():
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser(description="Update manifest after a batch-file-notes run")
    parser.add_argument("--manifest", default="./code-reading-notes/manifest.json", help="Path to manifest.json")
    parser.add_argument("--batch-size", type=int, required=True, help="Number of files attempted in the batch")
    parser.add_argument("--completed", default="", help="Comma-separated repo-relative file paths completed in the batch")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    manifest = load_manifest(manifest_path)

    completed = parse_completed(args.completed)
    batch = manifest.setdefault("batch", {})
    batch["last_batch_size"] = args.batch_size
    batch["last_completed_files"] = completed
    batch["last_processed_at"] = now_iso()

    progress = manifest.setdefault("progress", {})
    progress["last_skill"] = "batch-file-notes"
    progress["updated_at"] = now_iso()

    save_manifest(manifest_path, manifest)

    print(json.dumps({
        "manifest": str(manifest_path),
        "last_batch_size": args.batch_size,
        "last_completed_files": completed,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
