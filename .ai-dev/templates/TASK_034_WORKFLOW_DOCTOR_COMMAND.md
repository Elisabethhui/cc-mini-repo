# Current Task: task-034

## Goal

Wire workflow doctor into the command surface.

## Depends On

- task-033 workflow doctor core

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `src/core/workflow_doctor.py`
- `src/core/commands.py`
- `src/core/main.py`
- `tests/test_workflow_doctor.py`
- `tests/test_commands.py`

## Allowed Edit

- `src/core/commands.py`
- `tests/test_commands.py`

Optional:

- `src/core/main.py`
- `tests/test_main.py`

## Do Not Do

- Do not add auto-fix.
- Do not change init/status behavior except command registration if required.

## Acceptance Criteria

- User can invoke workflow doctor.
- Output is concise and severity-based.
- Command is read-only.
- Tests cover command route.

## Test Plan

```bash
pytest tests/test_workflow_doctor.py -v
pytest tests/test_commands.py -v
```

## Rollback

```bash
git restore src/core/commands.py tests/test_commands.py
git restore src/core/main.py tests/test_main.py
```
