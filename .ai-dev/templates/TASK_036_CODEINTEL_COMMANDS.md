# Current Task: task-036

## Goal

Expose the CodeIntel provider through a small command surface.

Start with read-only commands for status and query.

## Depends On

- task-035 CodeIntel provider core

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `src/core/codeintel.py`
- `src/core/commands.py`
- `src/core/main.py`
- `tests/test_codeintel.py`
- `tests/test_commands.py`

## Allowed Edit

- `src/core/commands.py`
- `tests/test_commands.py`

Optional:

- `src/core/main.py`
- `tests/test_main.py`

## Do Not Do

- Do not add context pack generation.
- Do not add automatic source reading.
- Do not require CodeGraph to be installed.
- Do not output huge raw query results.

## Acceptance Criteria

- User can ask for CodeIntel status.
- User can run a keyword query.
- Output is compact.
- Missing CodeGraph falls back or warns clearly.
- Tests cover command route.

## Test Plan

```bash
pytest tests/test_codeintel.py -v
pytest tests/test_commands.py -v
```

## Rollback

```bash
git restore src/core/commands.py tests/test_commands.py
git restore src/core/main.py tests/test_main.py
```
