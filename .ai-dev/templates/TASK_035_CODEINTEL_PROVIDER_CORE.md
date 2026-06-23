# Current Task: task-035

## Goal

Implement the first small CodeIntel provider core with CodeGraph detection, CodeGraph query, and rg fallback.

## Depends On

- `.ai-dev/design/CODEINTEL_PROVIDER_IMPLEMENTATION_PLAN.md`

## Context Budget

- model_context: 32k
- max_files_to_read: 5
- max_files_to_edit: 3

## Allowed Read

- `.ai-dev/design/CODEINTEL_PROVIDER_IMPLEMENTATION_PLAN.md`
- `src/core/tools/grep_tool.py`
- `src/core/commands.py`
- `tests/test_tools.py`
- `pyproject.toml`

## Allowed Edit

- `src/core/codeintel.py`
- `tests/test_codeintel.py`

## Do Not Do

- Do not implement MCP client.
- Do not implement full impact/call graph.
- Do not require CodeGraph for operation.
- Do not expose huge raw output.
- Do not use shell=True unless the project pattern requires it.

## Acceptance Criteria

- Detects CodeGraph unavailable.
- Runs CodeGraph status/query when available.
- Falls back to rg for keyword search.
- Applies timeouts and output limits.
- Returns compact structured results.
- Has tests with mocked subprocess.

## Test Plan

```bash
pytest tests/test_codeintel.py -v
```

## Map Sync

```bash
codegraph sync
codegraph status
```

## Rollback

```bash
git restore src/core/codeintel.py tests/test_codeintel.py
```
