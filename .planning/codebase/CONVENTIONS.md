# Coding Conventions

**Analysis Date:** 2026-04-18

## Languages

**Primary:** Python 3.11+
- `from __future__ import annotations` is used at the top of nearly every module for PEP 563 postponed annotation evaluation.
- Union syntax uses `|` (e.g., `str | None`) rather than `typing.Optional` or `typing.Union`.

## Naming Patterns

**Files:**
- Snake case: `file_edit.py`, `token_budget.py`, `test_engine.py`
- Tool modules prefixed with their category: `file_read.py`, `file_write.py`, `glob_tool.py`, `grep_tool.py`
- Test files prefixed with `test_`: `test_engine.py`, `test_tools.py`

**Classes:**
- PascalCase for all classes: `Engine`, `ToolResult`, `TokenBudgetManager`, `BudgetDecision`
- Abstract base classes use `ABC`: `Tool` in `src/core/tools/base.py`
- Dataclasses are preferred for data containers: `AppConfig`, `SessionMeta`, `LLMUsage`

**Functions / Methods:**
- Snake case: `submit()`, `execute()`, `estimate_from_messages()`
- Private helpers prefixed with underscore: `_normalize_content_block()`, `_value()`, `_count_message_chars()`
- Properties used for computed attributes: `PermissionChecker.ok`, `SandboxManager.config`

**Variables:**
- Snake case: `tool_uses`, `tool_results`, `batches`
- Type aliases use PascalCase: `ProviderName = str`, `PermissionBehavior = Literal["allow", "deny"]`
- Constants at module level use UPPER_CASE with leading underscore for internal: `_MAX_RETRIES`, `_RETRY_BACKOFF`, `_DEFAULT_TIMEOUT`

**Types:**
- `str | None` over `Optional[str]`
- `list[dict[str, Any]]` over `List[Dict[str, Any]]`
- `TYPE_CHECKING` blocks for imports that are only needed for type hints

## Code Style

**Formatting:**
- No explicit formatter configured (no `.prettierrc`, `.eslintrc`, `biome.json`, or `ruff.toml` detected).
- Line length appears to follow ~100 characters informally.
- Indentation: 4 spaces.

**Import Organization:**
1. `from __future__ import annotations`
2. Standard library imports
3. Third-party imports (e.g., `anthropic`, `openai`, `prompt_toolkit`, `rich`)
4. Local / relative imports

Example from `src/core/llm.py`:
```python
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Iterator

import anthropic
import httpx

try:
    from openai import OpenAI
    import openai
except Exception as exc:
    ...
```

**Path Aliases:**
- No import path aliases (e.g., `@/core/...`) are used.
- Absolute imports from the package root: `from core.engine import Engine`, `from core.tools.base import Tool, ToolResult`
- Relative imports within subpackages: `from .base import Tool, ToolResult`

## Error Handling

**Patterns:**
- Tools return `ToolResult(content=..., is_error=True)` rather than raising exceptions for expected failures (file not found, permission denied).
- The engine catches exceptions in `_execute_tool()` and wraps them in `ToolResult`:
  ```python
  except Exception as e:
      return ToolResult(content=f"Tool error: {e}", is_error=True)
  ```
- API errors are classified by `LLMClient.is_authentication_error()`, `is_retryable_error()`, `is_api_error()`.
- Retry logic uses exponential-ish backoff: `_RETRY_BACKOFF = (1, 3, 10)` in `src/core/engine.py`.
- Silent swallowing for non-critical persistence failures:
  ```python
  try:
      self._session_store.append_message(message)
  except Exception:
      pass
  ```

## Type Hints

- Functions and methods are fully type-annotated in core modules.
- `Any` is used sparingly for SDK objects that lack stable types.
- `TYPE_CHECKING` guards circular imports:
  ```python
  if TYPE_CHECKING:
      from .cost_tracker import CostTracker
      from .session import SessionStore
  ```

## Logging

**Framework:** `rich.console.Console` for terminal output, not the standard `logging` module.

**Patterns:**
- `Console().print(...)` is used for user-facing status and permission prompts.
- No structured logging or log levels observed.
- Debug output uses plain `print()` in some budget-protection paths (e.g., `src/core/engine.py` lines 268, 282, 284).

## Comments

**When to Comment:**
- Docstrings for public functions and classes (Google-style / plain descriptions).
- Chinese comments appear in recently added budget-protection and wiki-strict code (e.g., `src/core/engine.py`, `src/core/wiki/taskpack.py`).
- Section dividers with long comment banners:
  ```python
  # ---------------------------------------------------------------------------
  # Section Name
  # ---------------------------------------------------------------------------
  ```

**JSDoc/TSDoc:**
- Not applicable (Python project).
- Python docstrings are plain text, not reStructuredText or Google-style with type fields.

## Function Design

**Size:**
- Functions tend to be medium-length (20-60 lines).
- The `Engine.submit()` method in `src/core/engine.py` is a notable exception at ~350 lines; it contains the full streaming loop, retry logic, token budget checks, and tool execution.

**Parameters:**
- Keyword-only arguments for public APIs where order matters: `def create_message(self, *, model: str, max_tokens: int, ...)`
- Default values for optional config: `thresholds: BudgetThresholds | None = None`

**Return Values:**
- Iterators (`Iterator[tuple]`) are used for streaming events from `Engine.submit()`.
- `ToolResult` dataclass is the universal return type for tool execution.

## Module Design

**Exports:**
- No `__all__` declarations observed.
- Public API is implicit: anything not prefixed with `_` is public.

**Barrel Files:**
- `src/core/tools/__init__.py` exists but is empty (no re-exports).
- Subpackages like `src/core/sandbox/` and `src/core/wiki/` import explicitly from child modules.

## Special Conventions

**Tool Base Class:**
All tools inherit from `Tool` in `src/core/tools/base.py` and implement:
- `name` (property)
- `description` (property)
- `input_schema` (property)
- `execute(self, **kwargs) -> ToolResult`
- Optionally `is_read_only() -> bool` and `get_activity_description(**kwargs) -> str | None`

**Wiki-Strict Mode:**
- `RunMode` enum in `src/core/config.py` distinguishes `STANDARD` vs `WIKI_STRICT`.
- Environment variable `CC_MINI_MODE` controls mode selection.
- `FileEditTool` in `src/core/tools/file_edit_strict.py` adds backup, preview diff, and human-intervention fallback for wiki-strict editing.

**Session Persistence:**
- JSONL-based storage in `~/.mini-claude/sessions/`.
- `SessionStore` uses `@dataclass` for metadata and classmethods for reading.

---

*Convention analysis: 2026-04-18*
