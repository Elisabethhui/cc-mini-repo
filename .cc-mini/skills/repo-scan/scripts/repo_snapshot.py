#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from collections import Counter
from pathlib import Path
from typing import Iterable

DEFAULT_IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".idea",
    ".vscode",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".next",
    ".venv",
    "venv",
    ".mypy_cache",
    ".pytest_cache",
    ".cc-mini",
    "code-reading-notes",
}


def iter_files(root: Path) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in DEFAULT_IGNORE_DIRS]
        for name in filenames:
            yield Path(dirpath) / name


def top_level_summary(root: Path) -> list[dict]:
    rows: list[dict] = []
    for p in sorted(root.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
        if p.name in DEFAULT_IGNORE_DIRS:
            continue
        rows.append({"name": p.name, "type": "dir" if p.is_dir() else "file"})
    return rows


def likely_entry_files(files: list[Path], root: Path) -> list[str]:
    candidates: list[str] = []
    names = {
        "main.py",
        "app.py",
        "cli.py",
        "run.py",
        "manage.py",
        "server.py",
        "index.js",
        "index.ts",
        "main.ts",
        "main.js",
        "package.json",
        "pyproject.toml",
        "setup.py",
        "Cargo.toml",
        "pom.xml",
        "build.gradle",
    }
    for f in files:
        if f.name in names:
            candidates.append(str(f.relative_to(root)))
    return sorted(set(candidates))


def likely_config_files(files: list[Path], root: Path) -> list[str]:
    patterns = {
        "config.py",
        "settings.py",
        ".env",
        ".env.example",
        "pyproject.toml",
        "requirements.txt",
        "package.json",
        "tsconfig.json",
        "vite.config.ts",
        "vite.config.js",
        "webpack.config.js",
        "docker-compose.yml",
        "Dockerfile",
    }
    out: list[str] = []
    for f in files:
        if f.name in patterns:
            out.append(str(f.relative_to(root)))
    return sorted(set(out))


def largest_files(files: list[Path], root: Path, limit: int = 20) -> list[dict]:
    rows = []
    for f in files:
        try:
            st = f.stat()
        except OSError:
            continue
        rows.append({"path": str(f.relative_to(root)), "size_bytes": st.st_size})
    rows.sort(key=lambda x: x["size_bytes"], reverse=True)
    return rows[:limit]


def extension_stats(files: list[Path]) -> dict[str, int]:
    c = Counter()
    for f in files:
        ext = f.suffix.lower() or "[no_ext]"
        c[ext] += 1
    return dict(c.most_common(30))


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a lightweight repository snapshot")
    parser.add_argument("--repo", default=".", help="Repository path (default: current directory)")
    args = parser.parse_args()

    root = Path(args.repo).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Invalid repository path: {root}")

    files = list(iter_files(root))
    snapshot = {
        "repo_root": str(root),
        "top_level": top_level_summary(root),
        "file_count": len(files),
        "likely_entry_files": likely_entry_files(files, root),
        "likely_config_files": likely_config_files(files, root),
        "largest_files": largest_files(files, root),
        "extension_stats": extension_stats(files),
    }
    print(json.dumps(snapshot, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
