# Testing Registry

## Purpose

This file records the preferred test commands and test selection rules for cc-mini.

Use it with `test-gate` after each context-bounded task.

## Testing Principle

Run the smallest useful verification first.

Do not jump to the full suite unless the task is broad or the targeted tests are insufficient.

## Setup

Install in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

If needed, ensure imports resolve from `src`:

```bash
PYTHONPATH=src python -m core.main --help
```

## Main Test Commands

Run all tests:

```bash
pytest tests/ -v
```

Skip integration-style tests:

```bash
pytest tests/ -v -k "not integration"
```

Run one test file:

```bash
pytest tests/test_engine.py -v
```

Run one test:

```bash
pytest tests/test_engine.py::test_name -v
```

Run tests under `tests/core/`:

```bash
pytest tests/core/ -v
```

## Smoke Commands

CLI import/startup smoke check:

```bash
PYTHONPATH=src python -m core.main --help
```

Package import smoke check:

```bash
PYTHONPATH=src python -c "import core; print('ok')"
```

If console script is installed:

```bash
cc-mini --help
```

## Test Selection Rules

### Source File Changed

If one source file changed, look for a matching test file.

Examples:

- `src/core/engine.py` -> `tests/test_engine.py`
- `src/core/config.py` -> `tests/test_config.py`
- `src/core/context.py` -> `tests/test_context.py`
- `src/core/commands.py` -> `tests/test_commands.py`
- `src/core/permissions.py` -> `tests/test_permissions.py`
- `src/core/skills.py` -> `tests/test_skills.py`
- `src/core/token_budget.py` -> `tests/core/test_token_budget.py`
- `src/core/checkpoint.py` -> `tests/core/test_checkpoint.py`

### Tool Changed

If a tool changed under `src/core/tools/`, start with:

```bash
pytest tests/test_tools.py -v
```

Also consider:

```bash
pytest tests/test_permissions.py -v
```

if permissions or read/write behavior changed.

### Engine Changed

If `src/core/engine.py` changed, start with:

```bash
pytest tests/test_engine.py -v
```

Also consider:

```bash
pytest tests/core/test_engine_runtime_budget.py -v
```

if budget/runtime behavior changed.

### Main CLI Changed

If `src/core/main.py` changed, start with:

```bash
pytest tests/test_main.py -v
pytest tests/core/test_main_autocompact.py -v
```

Also run a smoke command:

```bash
PYTHONPATH=src python -m core.main --help
```

### Token Budget Changed

If `src/core/token_budget.py` changed, start with:

```bash
pytest tests/core/test_token_budget.py -v
pytest tests/core/test_engine_runtime_budget.py -v
```

### Compact Or Dehydration Changed

If compact/dehydration changed, start with:

```bash
pytest tests/core/test_compact_runtime.py -v
pytest tests/core/test_dehydration.py -v
```

### Session Or Memory Changed

If session or memory changed, consider:

```bash
pytest tests/test_session_mode.py -v
pytest tests/test_maintenance.py -v
```

### Sandbox Changed

If sandbox code changed, consider:

```bash
pytest tests/test_sandbox_checker.py -v
pytest tests/test_sandbox_command_matcher.py -v
pytest tests/test_sandbox_config.py -v
pytest tests/test_sandbox_manager.py -v
pytest tests/test_sandbox_wrapper.py -v
```

Only run sandbox integration tests when the environment supports them.

### Wiki-Strict Changed

If `src/core/wiki/` or `src/core/knowledge/` changed, start with:

```bash
pytest tests/test_wiki_phase1.py -v
pytest tests/test_wiki_phase3.py -v
pytest tests/test_wiki_phase6.py -v
```

### Worker Manager Changed

If `src/core/worker_manager.py` changed, start with:

```bash
pytest tests/test_worker_manager.py -v
pytest tests/core/test_worker_manager_checkpoint.py -v
```

### Buddy Changed

If `src/core/buddy/` changed, start with:

```bash
pytest tests/test_buddy_companion.py -v
pytest tests/test_buddy_mood.py -v
pytest tests/test_buddy_storage.py -v
```

## CodeGraph Affected Tests

After implementation and map sync:

```bash
git diff --name-only | codegraph affected --stdin --quiet
```

If this returns test files, run them first:

```bash
pytest <affected-test-file> -v
```

If it returns nothing but the change is non-trivial, use the manual mapping above.

## Verification Levels

Record one of these in test-gate:

- `none`: no verification was run
- `manual`: behavior checked manually
- `smoke`: startup/import/basic command passed
- `unit`: targeted unit tests passed
- `integration`: integration-style tests passed
- `full`: broad suite passed

Recommended minimum:

- docs/workflow-only change: `manual` or `smoke`
- small logic change: `unit`
- CLI behavior change: `unit` plus `smoke`
- sandbox/process behavior: targeted unit plus environment-aware integration if available
- public API/config behavior: targeted unit plus broader nearby tests

## Failure Classification

Classify failures as:

- task-related
- pre-existing
- environment/dependency
- flaky/timeout
- unclear

If unclear, do not expand scope automatically.

Stop after two failed focused fixes.

## Test Gate Output

Use `.ai-dev/templates/TEST_GATE.md` for task-level verification notes.

Local test notes belong in:

- `.ai-dev/worklogs/`
- `.ai-dev/tmp/`

Do not commit raw logs unless explicitly requested.

## Before Commit

Before commit, verify:

```bash
git status --short
git diff --stat
```

If product code changed, ensure test-gate has:

- selected verification
- command run
- pass/fail result
- verification level
- risk note