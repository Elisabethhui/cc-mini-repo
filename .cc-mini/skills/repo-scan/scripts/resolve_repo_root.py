#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def detect_repo_root(start: Path) -> Path:
    start = start.resolve()
    current = start
    markers = [".git", "pyproject.toml", "package.json", "Cargo.toml", "pom.xml"]
    while True:
        if any((current / marker).exists() for marker in markers):
            return current
        if current.parent == current:
            return start
        current = current.parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve canonical repository root")
    parser.add_argument("--repo", default=".", help="Optional repo path, otherwise current directory")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    raw = Path(args.repo).expanduser()
    if raw.exists():
        root = detect_repo_root(raw if raw.is_dir() else raw.parent)
    else:
        raise SystemExit(f"Path does not exist: {raw}")

    if args.format == "json":
        print(json.dumps({"repo_root": str(root)}, ensure_ascii=False, indent=2))
    else:
        print(str(root))


if __name__ == "__main__":
    main()
