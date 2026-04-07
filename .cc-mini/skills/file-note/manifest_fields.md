# Manifest fields for file-note

## Common fields
- `repo_root`: Absolute path to the project root.
- `files`: Dictionary keyed by repo-relative file path.
- `progress.last_skill`: Name of the most recently completed skill.
- `progress.updated_at`: ISO timestamp of last update.

## Skill-specific fields
- `files.<path>.status`: Set to done/failed/skipped after processing one file.
- `files.<path>.note_file`: Output markdown path for this file note.
- `files.<path>.last_processed_at`: ISO timestamp for last file-note run.
