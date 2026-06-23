# Current Task: task-038

## Goal

Wire test selector into a read-only workflow test recommendation command.

The command recommends tests; it does not run them automatically in v1.

## Depends On

- task-037 test selector core

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `src/core/test_selector.py`
- `src/core/commands.py`
- `tests/test_test_selector.py`
- `tests/test_commands.py`

## Allowed Edit

- `src/core/commands.py`
- `tests/test_commands.py`

Optional:

- `src/core/main.py`
- `tests/test_main.py`

## Do Not Do

- Do not execute tests automatically.
- Do not add review or logging.
- Do not mutate local task files.

## Acceptance Criteria

- Command recommends test commands from current diff or passed files.
- Output includes confidence and fallback reason.
- Missing CodeGraph does not fail.
- Tests cover route.

## Test Plan

```bash
pytest tests/test_test_selector.py -v
pytest tests/test_commands.py -v
```

## Rollback

```bash
git restore src/core/commands.py tests/test_commands.py
git restore src/core/main.py tests/test_main.py
```
