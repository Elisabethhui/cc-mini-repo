# Code Conventions — cc-mini

This document captures the code style, naming, patterns, and error handling conventions used across the cc-mini codebase.

---

## 1. Code Style

### 1.1 Imports

- **Always use `from __future__ import annotations`** as the first line in every module. This enables PEP 563 postponed annotation evaluation.
- Standard library imports come first, then third-party, then local project imports.
- Local imports use explicit relative imports within the `core` package: `from .llm import LLMClient`.
- Cross-subpackage imports also use relative form: `from .tools.base import Tool, ToolResult`.
- `TYPE_CHECKING` blocks are used aggressively to avoid circular imports for type-only references.

  Example from `src/core/permissions.py`:
  ```python
  from typing import Literal, TYPE_CHECKING
  from .tools.base import Tool

  if TYPE_CHECKING:
      from ._keylistener import EscListener
      from .sandbox.manager import SandboxManager
      from .plan import PlanModeManager
  ```

### 1.2 Typing

- Python 3.11+ union syntax is standard: `str | None`, `list[dict[str, Any]]`.
- `Any` is used pragmatically for SDK-normalized content blocks and config parsing.
- `Literal` is used for enumerated string values (e.g., `PermissionBehavior = Literal["allow", "deny"]`).
- Return type `...` (ellipsis) is used for abstract method stubs in ABCs.
- Type hints are present on public functions and class methods; private helpers may omit them when obvious.

### 1.3 Docstrings

- Module-level docstrings describe the file's purpose and often reference the corresponding TypeScript source in claude-code.
- Function docstrings use plain triple-quoted strings, not Google/NumPy style.
- Docstrings are concise — one or two sentences — and focus on "what", not "how".
- Internal helpers often have no docstring; behavior is inferred from the name.

  Example from `src/core/session.py`:
  ```python
  """Session persistence — JSONL-based conversation storage.

  Modelled after claude-code's ``src/utils/sessionStorage.ts``.
  Each session is a pair of files under ``~/.mini-claude/sessions/{sanitized_cwd}/``:
  ...
  """
  ```

### 1.4 Comments

- Inline comments in Chinese are present in some newer modules (token budget, dehydration, checkpoint) where the original author added explanations.
- English is the dominant language; Chinese comments appear in Phase-2+ additions (wiki-strict mode, local model support).
- Section dividers use long comment banners:
  ```python
  # ---------------------------------------------------------------------------
  # Constants
  # ---------------------------------------------------------------------------
  ```

---

## 2. Naming Conventions

### 2.1 Modules

- All lowercase with underscores: `file_read.py`, `token_budget.py`, `worker_manager.py`.
- Private/internal modules prefixed with underscore: `_keylistener.py`.

### 2.2 Classes

- PascalCase for all classes.
- Abstract base classes use `ABC` and `abstractmethod` but are not prefixed with "Abstract".
- Dataclasses are preferred for simple data containers: `ToolResult`, `AppConfig`, `BudgetDecision`.

  | Class | File | Role |
  |-------|------|------|
  | `Engine` | `engine.py` | Core streaming loop |
  | `Tool` | `tools/base.py` | Abstract tool base |
  | `LLMClient` | `llm.py` | Provider abstraction |
  | `PermissionChecker` | `permissions.py` | Permission gating |
  | `TokenBudgetManager` | `token_budget.py` | Context budget |
  | `CompactService` | `compact.py` | Context compression |
  | `SessionStore` | `session.py` | Persistence |
  | `WorkerManager` | `worker_manager.py` | Background workers |
  | `CostTracker` | `cost_tracker.py` | Token/cost tracking |
  | `CheckpointManager` | `checkpoint.py` | OOM checkpointing |

### 2.3 Functions and Methods

- snake_case for all functions and methods.
- Private helpers prefixed with underscore: `_load_file_values`, `_normalize_content_block`, `_count_message_chars`.
- Static methods used for pure utility functions on classes: `CostTracker.calculate_cost`.
- Properties expose computed state without side effects: `Engine.messages`, `Engine.system_prompt`.

### 2.4 Variables and Constants

- Module-level constants use `SCREAMING_SNAKE_CASE`.
- Private constants use leading underscore: `_MAX_RETRIES`, `_RETRY_BACKOFF`, `_DEFAULT_TIMEOUT`.
- Configuration constants are grouped near the top of the module.

### 2.5 Enums

- `str, Enum` pattern is used for string-valued enums: `BudgetState`, `FlowState`, `RunMode`.
- Enum members are UPPERCASE: `BudgetState.NORMAL`, `FlowState.PLAN`.

---

## 3. Error Handling Patterns

### 3.1 Tool Execution

Tools never raise exceptions to the caller. All errors are captured in `ToolResult`:

```python
@dataclass
class ToolResult:
    content: str
    is_error: bool = False
```

Example from `src/core/tools/file_read.py`:
```python
try:
    content = path.read_text(encoding="utf-8", errors="replace")
except OSError as e:
    return ToolResult(content=f"Error reading file: {e}", is_error=True)
```

### 3.2 Engine Loop

The engine uses a retry loop with categorized error handling:

```python
for attempt in range(_MAX_RETRIES):
    try:
        ...
    except AbortedError:
        raise
    except Exception as e:
        if self._client.is_authentication_error(e):
            ...
        if self._client.is_retryable_error(e):
            ...
        if self._client.is_api_error(e):
            ...
```

Non-retryable API errors pop the user message and yield an error event.

### 3.3 Silent Failure for Non-Critical Paths

Session persistence and cost tracking use bare `except Exception: pass` for non-critical paths:

```python
def _persist(self, message: dict) -> None:
    if self._session_store is not None:
        try:
            self._session_store.append_message(message)
        except Exception:
            pass
```

### 3.4 Config Parsing

Config parsing raises `ValueError` with descriptive messages for invalid input:

```python
raise ValueError(f"Invalid max_tokens value: {raw_value!r}") from exc
raise ValueError("max_tokens must be a positive integer")
```

### 3.5 Custom Exceptions

A single custom exception is defined for user-initiated abort:

```python
class AbortedError(Exception):
    """Raised when the current turn is aborted by the user (Esc / Ctrl+C)."""
```

---

## 4. Class and Interface Patterns

### 4.1 Tool Base Class

All tools inherit from `Tool` (`src/core/tools/base.py`) and implement:

```python
class Tool(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def input_schema(self) -> dict: ...

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult: ...

    def get_activity_description(self, **kwargs) -> str | None:
        return None

    def is_read_only(self) -> bool:
        return False

    def to_api_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }
```

Tools that are read-only override `is_read_only() -> True`. This drives the permission system.

### 4.2 Dataclass-Heavy Design

Simple data is stored in dataclasses rather than dicts:

- `AppConfig` (`config.py`)
- `LLMUsage`, `LLMMessage` (`llm.py`)
- `BudgetThresholds`, `BudgetDecision` (`token_budget.py`)
- `ModelUsage` (`cost_tracker.py`)
- `SessionMeta` (`session.py`)
- `WorkerUsage`, `WorkerTask` (`worker_manager.py`)
- `DehydrationResult` (`dehydration.py`)

### 4.3 Manager Pattern

Several subsystems use a "Manager" class that encapsulates state and lifecycle:

- `PermissionChecker` — permission decisions
- `TokenBudgetManager` — token estimation and budget decisions
- `CheckpointManager` — checkpoint file I/O
- `WorkerManager` — background thread pool for agent workers
- `PlanModeManager` — plan mode state machine
- `SandboxManager` — sandbox configuration and wrapping

### 4.4 Service Pattern

`CompactService` (`compact.py`) is a stateless service class that takes dependencies via constructor injection.

### 4.5 Registry Pattern

The skill system uses a module-level global registry:

```python
_REGISTRY: dict[str, Skill] = {}

def register_skill(skill: Skill) -> None: ...
def get_skill(name: str) -> Skill | None: ...
def list_skills(...) -> list[Skill]: ...
```

Tests use `clear_skills()` and an `autouse` fixture to isolate the registry.

### 4.6 Context Bundle

Command handlers receive a `CommandContext` dataclass rather than individual arguments:

```python
@dataclass
class CommandContext:
    engine: Engine
    session_store: SessionStore | None
    compact_service: CompactService
    console: Console
    app_config: AppConfig
    ...
```

---

## 5. File Organization

### 5.1 Source Layout

```
src/core/
  main.py              # CLI entry, REPL
  engine.py            # Streaming API loop
  llm.py               # Anthropic/OpenAI client abstraction
  config.py            # Configuration loading
  context.py           # System prompt builder
  commands.py          # Slash command parsing/dispatch
  session.py           # Session persistence
  compact.py           # Context compression
  coordinator.py       # Coordinator mode, worker prompts
  worker_manager.py    # Background worker threads
  permissions.py       # Permission gating
  cost_tracker.py      # Token/cost tracking
  token_budget.py      # Budget estimation
  checkpoint.py        # OOM checkpointing
  dehydration.py       # Message dehydration
  flow_state.py        # Wiki-strict state machine
  plan.py              # Plan mode manager
  memory.py            # KAIROS memory system
  skills.py            # Skill registry
  skills_bundled.py    # Built-in skills
  _keylistener.py      # ESC key listener
  tools/               # Tool implementations
    base.py
    file_read.py
    file_edit.py
    file_edit_strict.py
    file_write.py
    bash.py
    glob_tool.py
    grep_tool.py
    ask_user.py
    agent.py
    ast_read.py
    plan_tools.py
    reanchor.py
    error_handler.py
  sandbox/             # Bubblewrap sandbox
    config.py
    manager.py
    wrapper.py
    checker.py
  wiki/                # Wiki-strict subsystems
    taskpack.py
    reconcile.py
    archive.py
    query_archive.py
    lint.py
    maintenance.py
    post_edit_guard.py
    target_identity.py
  knowledge/           # Knowledge system
    ingester.py
    watcher.py
    dehydrator.py
  buddy/               # Companion system
    companion.py
    storage.py
    types.py
    prompt.py
```

### 5.2 Test Layout

```
tests/
  conftest.py          # Shared fixtures and dummy classes
  test_engine.py       # Engine loop tests
  test_llm.py          # LLM normalization tests
  test_config.py       # Config loading tests
  test_tools.py        # Tool execution tests
  test_permissions.py  # Permission logic tests
  test_context.py      # System prompt tests
  test_skills.py       # Skill registry tests
  test_cost_tracker.py # Cost calculation tests
  test_main.py         # CLI/REPL tests
  test_coordinator.py  # Coordinator mode tests
  test_worker_manager.py # Worker thread tests
  test_sandbox_*.py    # Sandbox unit + integration tests
  test_buddy_*.py      # Companion system tests
  core/                # Core subsystem tests
    test_checkpoint.py
    test_compact_runtime.py
    test_dehydration.py
    test_engine_runtime_budget.py
    test_main_autocompact.py
    test_token_budget.py
    test_worker_manager_checkpoint.py
```

---

## 6. Notable Patterns

### 6.1 SDK Normalization

The engine normalizes Anthropic SDK objects (Pydantic models) into plain dicts before storing messages. This avoids serialization issues and makes the codebase SDK-agnostic:

```python
def _normalize_json_value(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _normalize_json_value(value.model_dump())
    if hasattr(value, "dict"):
        return _normalize_json_value(value.dict())
    ...
```

### 6.2 Event Yielding

The engine communicates with the REPL via yielded tuples rather than callbacks or async:

```python
def submit(self, user_input: str) -> Iterator[tuple]:
    ...
    yield ("text", text)
    yield ("tool_call", tool_name, tool_input, activity)
    yield ("tool_result", tool_name, tool_input, result)
    yield ("usage", usage)
    yield ("error", message)
```

### 6.3 Monkeypatching in Tests

Tests frequently use `pytest.MonkeyPatch` and `unittest.mock.patch` to stub external dependencies (subprocess, filesystem, API clients).

### 6.4 String Constants for Tool Names

Tool names are string constants defined on the class, not enums:

```python
class FileReadTool(Tool):
    name = "Read"
```

This allows the permission system and engine to look up tools by name in a dict: `self._tools = {t.name: t for t in tools}`.
