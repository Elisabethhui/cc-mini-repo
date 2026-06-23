# Current Task: task-031

## Goal

Implement the core read-only/planned-safe file generation logic for `workflow init`.

This task should add helper functions that calculate what workflow files are missing and prepare write plans. It should not wire the user-facing command yet unless trivial.

## Depends On

- `.ai-dev/design/WORKFLOW_INIT_PLAN.md`
- workflow status implementation

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `src/core/workflow_status.py`
- `src/core/commands.py`
- `tests/test_workflow_status.py`
- `.ai-dev/design/WORKFLOW_INIT_PLAN.md`
- `.ai-dev/WORKFLOW.md`

## Allowed Edit

Preferred:

- `src/core/workflow_init.py`
- `tests/test_workflow_init.py`

Optional:

- `src/core/workflow_status.py`

## Do Not Do

- Do not wire CLI command yet unless clearly tiny.
- Do not overwrite existing files by default.
- Do not modify product source outside allowed files.
- Do not auto-commit.
- Do not initialize CodeGraph.

## Acceptance Criteria

- Can compute missing workflow files for a root.
- Can create missing files in a temporary directory.
- Does not overwrite existing files by default.
- Returns created/skipped/conflict results.
- Has unit tests with temporary directories.

## Test Plan

```bash
pytest tests/test_workflow_init.py -v
```

## Map Sync

After implementation:

```bash
codegraph sync
codegraph status
```

## Rollback

```bash
git restore src/core/workflow_init.py tests/test_workflow_init.py
git restore src/core/workflow_status.py
```
