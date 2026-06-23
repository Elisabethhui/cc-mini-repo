# Current Task: task-037

## Goal

Implement a read-only test selector core that recommends targeted tests from changed files.

## Depends On

- `.ai-dev/design/TEST_SELECTOR_PLAN.md`
- task-035 CodeIntel provider core

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `.ai-dev/TESTING.md`
- `.ai-dev/design/TEST_SELECTOR_PLAN.md`
- `src/core/codeintel.py`
- `tests/`

## Allowed Edit

- `src/core/test_selector.py`
- `tests/test_test_selector.py`

## Do Not Do

- Do not run tests automatically.
- Do not wire command yet.
- Do not require CodeGraph.
- Do not inspect huge files.

## Acceptance Criteria

- Recommends tests for known cc-mini source areas.
- Uses CodeGraph affected tests if available and fresh.
- Falls back to manual mapping.
- Returns confidence and warnings.
- Has unit tests.

## Test Plan

```bash
pytest tests/test_test_selector.py -v
```

## Rollback

```bash
git restore src/core/test_selector.py tests/test_test_selector.py
```
