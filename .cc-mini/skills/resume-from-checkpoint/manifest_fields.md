# Manifest fields for resume-from-checkpoint

## Required fields inspected
- `repo_root`: absolute project root
- `scan.done`: whether repository scan has completed
- `files`: per-file reading state
- `modules`: per-module state
- `project_summary.status`
- `interview_notes.status`
- `progress.last_skill`
- `progress.updated_at`

## Recovery-oriented derived checks
- whether `00_repo_scan/repo_snapshot.json` exists
- whether `00_repo_scan/repo_overview.md` exists
- whether any file notes exist under `10_file_notes/`
- whether any module notes exist under `20_module_notes/`
- whether project summary files exist
- whether interview files exist
- whether TODO and progress exist
