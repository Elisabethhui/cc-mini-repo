# Current Task: task-042

## Goal

Implement a read-only `workflow next` state recommendation core.

This is not full automation. It recommends the next workflow step from available artifacts and git state.

## Depends On

- `.ai-dev/design/STATE_ROUTER.md`

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `.ai-dev/design/STATE_ROUTER.md`
- `src/core/workflow_status.py`
- `src/core/workflow_doctor.py`
- `src/core/commands.py`

## Allowed Edit

- `src/core/workflow_next.py`
- `tests/test_workflow_next.py`

Optional:

- `src/core/commands.py`
- `tests/test_commands.py`

## Do Not Do

- Do not execute next step automatically.
- Do not edit files.
- Do not run tests.
- Do not commit.
- Do not rollback.

## Acceptance Criteria

- Infers coarse workflow state.
- Recommends next action.
- Prints stop condition.
- Requires user confirmation for risky actions.
- Has tests.

## Test Plan

```bash
pytest tests/test_workflow_next.py -v
```

## Rollback

```bash
git restore src/core/workflow_next.py tests/test_workflow_next.py
git restore src/core/commands.py tests/test_commands.py
```
