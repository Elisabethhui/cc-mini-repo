# Current Task: task-043

## Goal

Perform a read-only boundary review of existing wiki_strict modules and decide what should be kept, reduced, or replaced by context-bounded workflow.

## Depends On

- `.ai-dev/design/WIKI_STRICT_REDUCTION_PLAN.md`

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 1

## Allowed Read

- `src/core/wiki/`
- `src/core/knowledge/`
- `src/core/flow_state.py`
- `tests/test_wiki_phase1.py`
- `tests/test_wiki_phase3.py`
- `tests/test_wiki_phase6.py`

## Allowed Edit

- `.ai-dev/design/WIKI_STRICT_REDUCTION_PLAN.md`

## Do Not Do

- Do not modify product code.
- Do not delete wiki_strict code.
- Do not change tests.

## Acceptance Criteria

- Produces keep/reduce/replace table.
- Identifies first safe replacement candidate.
- Identifies risks and tests.

## Test Plan

No product tests required. This is read-only/design.

## Rollback

```bash
git restore .ai-dev/design/WIKI_STRICT_REDUCTION_PLAN.md
```
