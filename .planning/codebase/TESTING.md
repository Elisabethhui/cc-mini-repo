# Testing Patterns

**Analysis Date:** 2026-04-18

## Test Framework

**Runner:**
- pytest >= 8.0
- Config: `pyproject.toml` under `[tool.pytest.ini_options]`
  ```toml
  testpaths = ["tests"]
  pythonpath = ["src"]
  ```

**Assertion Library:**
- Built-in `assert` (pytest style)
- No `unittest.TestCase` subclasses observed in the main test suite

**Run Commands:**
```bash
pytest tests/ -v                    # Run all tests
pytest tests/ -v -k "not integration"  # Skip integration tests (sandbox/bwrap)
pytest tests/test_engine.py -v      # Run specific test file
pytest tests/test_engine.py::test_name -v  # Run specific test
```

## Test File Organization

**Location:**
- Co-located under `tests/` at project root, mirroring `src/` structure loosely.
- Core engine tests in `tests/core/` (e.g., `tests/core/test_dehydration.py`).
- Sandbox tests in `tests/test_sandbox_*.py`.

**Naming:**
- `test_<module>.py` for module-level tests.
- `test_<subsystem>_<aspect>.py` for focused tests (e.g., `test_sandbox_checker.py`).

**Structure:**
```
tests/
├── conftest.py                     # Shared fixtures and dummy classes
├── test_engine.py                  # Engine streaming loop tests
├── test_tools.py                   # Tool execution tests
├── test_permissions.py             # Permission checker tests
├── test_llm.py                     # LLM message normalization tests
├── test_config.py                  # Config loading tests
├── test_context.py                 # System prompt builder tests
├── test_cost_tracker.py            # Cost tracking tests
├── test_skills.py                  # Skill registry tests
├── test_coordinator.py             # Coordinator mode tests
├── test_worker_manager.py          # Background worker tests
├── test_main.py                    # CLI entry point tests
├── test_session_mode.py            # Session persistence tests
├── core/
│   ├── test_dehydration.py         # Message dehydration tests
│   ├── test_compact_runtime.py     # Context compaction tests
│   ├── test_engine_runtime_budget.py  # Token budget integration tests
│   └── test_token_budget.py        # Budget decision logic tests
└── test_sandbox_*.py               # Sandbox subsystem tests
```

## Test Structure

**Suite Organization:**
- Plain functions for simple tests.
- `class Test<Feature>:` groups for related tests (common in `test_skills.py`, `test_buddy_companion.py`, `test_cost_tracker.py`).

Example from `tests/test_skills.py`:
```python
class TestParseFrontmatter:
    def test_full_frontmatter(self):
        ...

class TestRegistry:
    def test_register_and_get(self):
        ...
```

**Setup / Teardown:**
- `pytest.fixture` for shared state.
- `autouse=True` fixture to clean global registries between tests:
  ```python
  @pytest.fixture(autouse=True)
  def _clean_registry():
      clear_skills()
      yield
      clear_skills()
  ```

## Mocking

**Framework:** `unittest.mock` (standard library) — `MagicMock`, `patch`, `PropertyMock`.

**Patterns:**
- Patch LLM client methods to simulate API responses:
  ```python
  with patch.object(engine._client, "stream_messages", return_value=_make_text_response("hello")):
      events = list(engine.submit("hi"))
  ```
- Monkeypatch environment variables and platform checks:
  ```python
  monkeypatch.setattr("core.sandbox.checker.platform.system", lambda: "Linux")
  monkeypatch.setattr("core.sandbox.checker.shutil.which", lambda x: None)
  ```
- Fake classes for terminal listeners to avoid TTY dependencies:
  ```python
  class _FakeEscListener:
      pressed = False
      def pause(self): pass
      def resume(self): pass
  ```

**What to Mock:**
- API streaming responses (`LLMClient.stream_messages`, `LLMClient.create_message`).
- Subprocess calls for git status / sandbox checks.
- Terminal input (`sys.stdin`, `EscListener`).
- File system via `tmp_path` / `tmp_path` fixtures.

**What NOT to Mock:**
- Actual tool execution on temporary files (tools read/write real `tmp_path` files).
- Dataclass construction and simple data transformations.

## Fixtures and Factories

**Test Data:**
- `tmp_path` (pytest built-in) for filesystem fixtures.
- `monkeypatch` for environment/config mutation.
- Custom fixtures in `tests/conftest.py`:
  - `tmp_repo` — creates a temporary repo with `code-reading-notes/manifest.json`.

**Dummy Classes in `tests/conftest.py`:**
```python
class DummyUsage:
    def __init__(self, input_tokens=0, output_tokens=0, ...):
        ...

class DummyClient:
    def stream_messages(self, **kwargs): ...
    def create_message(self, **kwargs): ...

class DummyPermissionChecker:
    def check(self, tool, tool_input): return self.decision

class DummyReadOnlyTool:
    name = "ReadOnlyDummy"
    def is_read_only(self): return True
    def execute(self, **kwargs): return ToolResult(content="x" * 1500)
```

## Coverage

**Requirements:** Not enforced in config.

**View Coverage:**
```bash
pytest tests/ --cov=core --cov-report=term-missing
```
(Requires `pytest-cov` to be installed; not in current `pyproject.toml` dependencies.)

## Test Types

**Unit Tests:**
- Majority of the suite.
- Test individual functions/classes in isolation with mocked dependencies.
- Examples: `test_llm.py` (message normalization), `test_cost_tracker.py` (pricing math), `test_tools.py` (tool execution on temp files).

**Integration Tests:**
- `tests/test_sandbox_integration.py` — requires `bwrap` binary; skipped when unavailable:
  ```python
  pytestmark = pytest.mark.skipif(not shutil.which("bwrap"), reason="bwrap not available")
  ```
- `tests/core/test_engine_runtime_budget.py` — tests full engine loop with dummy client and real checkpoint I/O.

**E2E Tests:**
- Not used.

## Common Patterns

**Async Testing:**
- Not applicable; the codebase uses synchronous generators (`Iterator[tuple]`) for streaming, not `async`/`await`.

**Error Testing:**
- Assert on `ToolResult.is_error`:
  ```python
  result = FileEditTool().execute(file_path="/nonexistent", old_string="x", new_string="y")
  assert result.is_error
  assert "not found" in result.content.lower()
  ```
- `pytest.raises(ValueError, match="...")` for config validation:
  ```python
  with pytest.raises(ValueError, match="Invalid max_tokens"):
      load_app_config(_args(config=str(config_path)))
  ```

**Event-Driven Testing:**
- `Engine.submit()` yields tuples; tests filter by event type:
  ```python
  events = list(engine.submit("hi"))
  text_events = [e for e in events if e[0] == "text"]
  tool_result_events = [e for e in events if e[0] == "tool_result"]
  ```

**State Mutation Testing:**
- Verify internal state after operations:
  ```python
  assert str(target) in eng._recent_written_artifacts
  assert target.exists()
  ```

---

*Testing analysis: 2026-04-18*
