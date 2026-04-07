#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

PRIORITY_ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}


def load_json(path: Path):
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def main() -> None:
    parser = argparse.ArgumentParser(description="Render TODO.md from manifest status")
    parser.add_argument("--manifest", default="./code-reading-notes/manifest.json", help="Path to manifest.json")
    parser.add_argument("--output", default="./code-reading-notes/TODO.md", help="Output TODO markdown path")
    parser.add_argument("--limit", type=int, default=30, help="Max pending file entries to render")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = load_json(manifest_path)

    pending_files = []
    for rel_path, meta in manifest.get("files", {}).items():
        status = meta.get("status", "pending")
        if status != "done":
            pending_files.append({
                "path": rel_path,
                "priority": meta.get("priority", "D"),
                "module": meta.get("module", ""),
                "status": status,
            })
    pending_files.sort(key=lambda x: (PRIORITY_ORDER.get(x["priority"], 99), x["path"]))

    pending_modules = []
    for name, meta in manifest.get("modules", {}).items():
        status = meta.get("status", "pending")
        if status != "done":
            pending_modules.append({
                "name": name,
                "status": status,
                "file_count": len(meta.get("files", [])),
            })
    pending_modules.sort(key=lambda x: x["name"])

    lines = [
        "# TODO",
        "",
        "## Pending files",
    ]
    if pending_files:
        for row in pending_files[:args.limit]:
            module_txt = f" | module: {row['module']}" if row["module"] else ""
            lines.append(f"- [ ] `{row['path']}` | priority: {row['priority']} | status: {row['status']}{module_txt}")
    else:
        lines.append("- No pending files")

    lines.extend(["", "## Pending modules"])
    if pending_modules:
        for row in pending_modules:
            lines.append(f"- [ ] `{row['name']}` | status: {row['status']} | files: {row['file_count']}")
    else:
        lines.append("- No pending modules")

    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output_path),
        "pending_files": len(pending_files),
        "pending_modules": len(pending_modules),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
