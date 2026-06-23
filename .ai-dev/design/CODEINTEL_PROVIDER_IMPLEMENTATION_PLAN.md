# CodeIntel Provider Implementation Plan

## Purpose

Plan the first implementation of a CodeIntel provider abstraction.

This turns CodeGraph usage from a written workflow into a reusable product capability.

## Goal

Add a small internal provider layer that can answer code intelligence questions without requiring the model to read large files.

## First Provider Scope

Implement only these first:

- detect CodeGraph availability
- detect `.codegraph/` initialization
- run `codegraph status`
- run `codegraph query <keyword>`
- fallback to `rg` when CodeGraph is unavailable

Do not implement full impact/call graph in the first pass.

## Non-Goals

Do not implement yet:

- full MCP client
- Codebase-Memory-MCP integration
- daemon management
- semantic search abstraction
- automatic context-pack generation
- automatic test selection

## Proposed Module

Recommended new file:

```text
src/core/codeintel.py
```

Possible types:

```python
@dataclass
class CodeIntelResult:
    provider: str
    query: str
    ok: bool
    items: list[str]
    warnings: list[str]
    truncated: bool = False

class CodeIntelProvider:
    def available(self) -> bool:
        ...

    def status(self) -> CodeIntelResult:
        ...

    def query(self, keyword: str) -> CodeIntelResult:
        ...
```

Keep it simple and consistent with existing project style.

## Provider Order

1. CodeGraph
2. rg fallback

If CodeGraph fails:

- record warning
- return fallback results
- do not crash

## Security And Safety

- use subprocess safely
- do not run shell=True unless existing project style requires it
- apply timeout
- trim output
- do not expose huge raw output
- never read `.codegraph/` database directly

## Output Limits

Default output limits:

- max items: 20
- max lines: 200
- max chars: small enough for a 32k context workflow

If output is truncated, set:

```text
truncated: true
```

## Implementation Areas

Likely files:

- `src/core/codeintel.py`
- `tests/test_codeintel.py`

Optional later:

- `src/core/commands.py`

## Acceptance Criteria

- can detect CodeGraph missing
- can detect CodeGraph present
- can query via CodeGraph when available
- can fallback to `rg`
- returns compact structured result
- handles timeout/failure gracefully
- has tests with mocked subprocess

## Test Plan

```bash
pytest tests/test_codeintel.py -v
```

Test cases:

- CodeGraph missing
- CodeGraph status success
- CodeGraph query success
- CodeGraph timeout
- CodeGraph error
- rg fallback success
- output truncation

## Map Sync

When this implementation changes product code:

```bash
codegraph sync
codegraph status
```

## First Executable Task

Create task:

`Task 035 - CodeIntel provider core`

Keep command wiring for a later task.
