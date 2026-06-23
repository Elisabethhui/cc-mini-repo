# Current Task: task-032

## Goal

Wire the workflow init core logic into the command surface.

## Depends On

- task-031 workflow init core

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `src/core/workflow_init.py`
- `src/core/workflow_status.py`
- `src/core/commands.py`
- `src/core/main.py`
- `tests/test_workflow_init.py`
- `tests/test_commands.py`

## Allowed Edit

- `src/core/commands.py`
- `tests/test_commands.py`

Optional if existing CLI routing requires:

- `src/core/main.py`
- `tests/test_main.py`

## Do Not Do

- Do not add task generation.
- Do not add context pack generation.
- Do not auto-initialize CodeGraph.
- Do not overwrite files without explicit user approval.

## Acceptance Criteria

- User can invoke workflow init through existing command surface.
- Command prints created/skipped/conflict summary.
- Existing files are preserved by default.
- Tests cover command route.

## Test Plan

```bash
pytest tests/test_workflow_init.py -v
pytest tests/test_commands.py -v
```

If `main.py` changes:

```bash
pytest tests/test_main.py -v
```

## Rollback

```bash
git restore src/core/commands.py tests/test_commands.py
git restore src/core/main.py tests/test_main.py
```
