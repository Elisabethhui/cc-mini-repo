# Manifest fields for this skill

## Common fields
- `repo_root`: Absolute path to the project root. All stored file paths in manifests should be repo-relative unless explicitly noted.
- `scan.done`: Whether `/repo-scan` has completed successfully.
- `scan.snapshot_file`: Path to `00_repo_scan/repo_snapshot.json`.
- `files`: Dictionary keyed by repo-relative file path.
- `files.<path>.priority`: Priority level: A, B, C, or D.
- `files.<path>.status`: pending | done | skipped | failed.
- `files.<path>.note_file`: Path to the generated file note markdown, if any.
- `files.<path>.module`: Module name assigned to the file.
- `modules`: Dictionary keyed by module name.
- `modules.<name>.status`: pending | done | skipped | failed.
- `modules.<name>.files`: List of repo-relative file paths in the module.
- `modules.<name>.note_file`: Path to the generated module note markdown, if any.
- `project_summary.status`: pending | done | failed.
- `project_summary.arch_file`: Path to `project_architecture.md`.
- `project_summary.highlights_file`: Path to `project_technical_highlights.md`.
- `interview_notes.status`: pending | done | failed.
- `interview_notes.files`: Paths to generated interview materials.
- `progress.last_skill`: Name of the most recently completed skill.
- `progress.updated_at`: ISO timestamp of last update.

## Skill-specific fields
- `progress.last_recommendation`: Suggested next skill and targets.