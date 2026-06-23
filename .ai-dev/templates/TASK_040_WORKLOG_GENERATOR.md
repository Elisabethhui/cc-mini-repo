# Current Task: task-040

## Goal

Implement a local ignored work-log generator for completed workflow tasks.

## Depends On

- work-log skill

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `.ai-dev/templates/WORK_LOG.md`
- `.ai-dev/skills/work-log/SKILL.md`
- `src/core/commands.py`

## Allowed Edit

- `src/core/work_log.py`
- `tests/test_work_log.py`

Optional command wiring:

- `src/core/commands.py`
- `tests/test_commands.py`

## Do Not Do

- Do not commit generated logs.
- Do not write outside `.ai-dev/worklogs/` by default.
- Do not include secrets or raw huge logs.

## Acceptance Criteria

- Can render compact work log text.
- Can write to `.ai-dev/worklogs/task-xxx.md`.
- Creates parent directory if needed.
- Keeps output short.
- Has tests with temporary directories.

## Test Plan

```bash
pytest tests/test_work_log.py -v
```

If command wiring is included:

```bash
pytest tests/test_commands.py -v
```

## Rollback

```bash
git restore src/core/work_log.py tests/test_work_log.py
git restore src/core/commands.py tests/test_commands.py
```
