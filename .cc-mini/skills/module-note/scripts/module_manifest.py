#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def load_json(path: Path) -> dict:
    if not path.exists():
        raise SystemExit(f"File not found: {path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def auto_module_name(rel_path: str) -> str:
    p = Path(rel_path)
    parts = p.parts
    if len(parts) == 1:
        stem = p.stem.lower()
        if stem in {"main", "app", "cli", "run"}:
            return "entry"
        if "config" in stem or "setting" in stem:
            return "config"
        return "root_files"

    head = parts[0].lower()
    aliases = {
        "core": "core_runtime",
        "agent": "agents",
        "agents": "agents",
        "tool": "tools",
        "tools": "tools",
        "api": "api",
        "service": "services",
        "services": "services",
        "memory": "memory",
        "config": "config",
        "configs": "config",
    }
    return aliases.get(head, head)


def build_module_candidates(manifest: dict) -> dict:
    files = manifest.get("files", {})
    grouped: dict[str, list[str]] = defaultdict(list)
    for rel_path, meta in files.items():
        module = meta.get("module") or auto_module_name(rel_path)
        grouped[module].append(rel_path)
    return {
        name: {"files": sorted(paths), "status": "pending"}
        for name, paths in sorted(grouped.items())
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Build or refresh module candidates from manifest files")
    parser.add_argument("--manifest", default="./code-reading-notes/manifest.json", help="Path to manifest.json")
    parser.add_argument("--output", default="./code-reading-notes/00_repo_scan/module_candidates.json", help="Output path")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    manifest = load_json(manifest_path)
    candidates = build_module_candidates(manifest)

    output_path.write_text(json.dumps(candidates, ensure_ascii=False, indent=2), encoding="utf-8")

    modules = manifest.setdefault("modules", {})
    for name, payload in candidates.items():
        entry = modules.setdefault(name, {})
        entry.setdefault("status", payload.get("status", "pending"))
        entry["files"] = payload["files"]

    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "manifest": str(manifest_path),
        "output": str(output_path),
        "module_count": len(candidates),
        "modules": list(candidates.keys()),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
