# Current Task: task-041

## Goal

Implement a read-only rollback helper that prints safe rollback suggestions for current workflow task changes.

## Depends On

- `.ai-dev/design/ROLLBACK_HELPER_PLAN.md`
- review-rollback skill

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `.ai-dev/design/ROLLBACK_HELPER_PLAN.md`
- `src/core/commands.py`
- existing git helper patterns if any

## Allowed Edit

- `src/core/rollback_helper.py`
- `tests/test_rollback_helper.py`

Optional:

- `src/core/commands.py`
- `tests/test_commands.py`

## Do Not Do

- Do not execute destructive git commands.
- Do not delete files.
- Do not auto-revert commits.
- Do not hide dirty worktree state.

## Acceptance Criteria

- Detects unstaged/staged changes.
- Prints suggested rollback commands.
- Warns before destructive operations.
- Handles no-git case gracefully.
- Has tests.

## Test Plan

```bash
pytest tests/test_rollback_helper.py -v
```

## Rollback

```bash
git restore src/core/rollback_helper.py tests/test_rollback_helper.py
git restore src/core/commands.py tests/test_commands.py
```
