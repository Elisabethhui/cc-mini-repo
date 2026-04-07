# Script responsibilities

| Script | Responsibility |
|---|---|
| `repo_snapshot.py` | Scan the repo tree, count files, detect entry/config candidates, and print a snapshot JSON. |
| `resolve_repo_root.py` | Resolve current working directory or argument into a canonical repo root path. |
| `init_manifest.py` | Create `manifest.json`, `TODO.md`, and `progress.md` if missing. |
