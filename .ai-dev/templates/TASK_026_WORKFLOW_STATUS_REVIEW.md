# Current Task: task-026

## Goal

Run the final map-sync, test-gate, fresh-review, and work-log pass for the `workflow status` feature after task-024 and task-025 are implemented.

This task does not add new feature behavior. It verifies, reviews, and closes out the first product implementation.

## Why

The workflow status feature is the first real product change in the context-bounded workflow system. It must prove that the process works end to end:

- implementation
- map sync
- targeted tests
- fresh review
- rollback path
- work log

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 1
- max_iterations: 1

## Depends On

- task-024 workflow status core module
- task-025 workflow status command wiring

## Allowed Read

- `src/core/workflow_status.py`
- `src/core/commands.py`
- `src/core/main.py` if changed
- `tests/test_workflow_status.py`
- `tests/test_commands.py`
- `tests/test_main.py` if changed
- relevant git diff

## Allowed Edit

Only local ignored artifacts unless a tiny documentation/workflow note is explicitly needed:

- `.ai-dev/worklogs/`
- `.ai-dev/tmp/`

Do not edit product code in this review task unless review finds a small blocking issue and the user explicitly approves a revise step.

## Do Not Do

- Do not add new workflow commands.
- Do not refactor command routing.
- Do not expand scope into workflow init.
- Do not change CodeGraph provider behavior.
- Do not commit local task artifacts.
- Do not ignore failed tests.

## Required Commands

```bash
git status --short
git diff --stat
git diff --name-only
```

If CodeGraph is available:

```bash
codegraph sync
codegraph status
git diff --name-only | codegraph affected --stdin --quiet
```

Run targeted tests:

```bash
pytest tests/test_workflow_status.py -v
pytest tests/test_commands.py -v
```

If `src/core/main.py` changed:

```bash
pytest tests/test_main.py -v
PYTHONPATH=src python -m core.main --help
```

## Fresh Review Packet

Include:

- original task goal
- changed files
- diff stat
- targeted tests run
- test result
- CodeGraph freshness state
- known risks
- rollback path

## Acceptance Criteria

- map-sync decision is recorded
- targeted tests are run or failure is classified
- fresh review recommendation is explicit
- no local workflow artifacts are staged
- rollback path is concrete
- commit decision is clear

## Review Decision

Use one:

- commit
- revise
- rollback
- reslice
- hold

## Rollback

Before commit:

```bash
git restore src/core/workflow_status.py tests/test_workflow_status.py
git restore src/core/commands.py tests/test_commands.py
```

If touched:

```bash
git restore src/core/main.py tests/test_main.py
```
