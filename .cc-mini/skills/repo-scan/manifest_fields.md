# Manifest fields for repo-scan

## Common fields
- `repo_root`: Absolute path to the project root.
- `scan.done`: Whether `/repo-scan` has completed successfully.
- `scan.snapshot_file`: Path to `00_repo_scan/repo_snapshot.json`.
- `files`: Dictionary keyed by repo-relative file path.
- `modules`: Dictionary keyed by module name.
- `progress.last_skill`: Name of the most recently completed skill.
- `progress.updated_at`: ISO timestamp of last update.

## Skill-specific fields
- `scan.entry_candidates`: List of likely entry files discovered by scan.
- `scan.config_candidates`: List of likely config files.
- `scan.module_candidates_file`: Path to `00_repo_scan/module_candidates.json`.
- `scan.reading_order_file`: Path to `00_repo_scan/reading_order.md`.
