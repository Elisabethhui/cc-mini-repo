#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Resolve a repo-relative target path into an absolute path")
    parser.add_argument("--repo-root", required=True, help="Absolute repository root")
    parser.add_argument("--target", required=True, help="Repository-relative file path")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    target_rel = Path(args.target)

    if target_rel.is_absolute():
        resolved = target_rel.resolve()
    else:
        resolved = (repo_root / target_rel).resolve()

    result = {
        "repo_root": str(repo_root),
        "target_rel": args.target,
        "target_abs": str(resolved),
        "exists": resolved.exists(),
        "is_file": resolved.is_file(),
    }

    if args.format == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(str(resolved))


if __name__ == "__main__":
    main()
