# Testing Conventions — cc-mini

This document describes the test framework, organization, mocking patterns, and coverage approach used in the cc-mini project.

---

## 1. Test Framework

### 1.1 pytest

- **Framework:** pytest (>= 8.0)
- **Async support:** pytest-asyncio (>= 0.23) is listed in dev dependencies but rarely used; the codebase prefers synchronous tests with threading.
- **Configuration:** `pyproject.toml`

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

### 1.2 Running Tests

```bash
# All tests
pytest tests/ -v

# Skip integration tests (sandbox/bwrap)
pytest tests/ -v -k "not integration"

# Specific file
pytest tests/test_engine.py -v

# Specific test
pytest tests/test_engine.py::test_name -v
```

### 1.3 Test Discovery

- Test files follow the `test_*.py` pattern.
- Test functions use `test_` prefix.
- Test classes use `Test` prefix (e.g., `TestParseFrontmatter`, `TestRegistry`).

---

## 2. Test Organization

### 2.1 Directory Structure

```
tests/
  __init__.py              # Empty marker
  conftest.py              # Shared fixtures and dummy classes
  test_engine.py           # Engine streaming loop
  test_llm.py              # LLM message normalization
  test_config.py           # Config loading and resolution
  test_tools.py            # Tool execution (Read, Edit, Bash, Glob, Grep)
  test_permissions.py      # Permission checker logic
  test_context.py          # System prompt construction
  test_skills.py           # Skill registry and bundled skills
  test_cost_tracker.py     # Cost calculation and formatting
  test_main.py             # CLI entry point and REPL events
  test_coordinator.py      # Coordinator mode and session matching
  test_worker_manager.py   # Background worker threads
  test_session_mode.py     # Session mode switching
  test_sandbox_manager.py  # Sandbox configuration
  test_sandbox_wrapper.py  # bwrap command building
  test_sandbox_checker.py  # Dependency checking
  test_sandbox_command_matcher.py  # Command allowlisting
  test_sandbox_config.py   # Config parsing
  test_sandbox_integration.py      # Integration tests requiring bwrap
  test_ask_user.py         # AskUserQuestion tool
  test_buddy_*.py          # Companion system tests
  core/                    # Core subsystem tests
    test_checkpoint.py
    test_compact_runtime.py
    test_dehydration.py
    test_engine_runtime_budget.py
    test_main_autocompact.py
    test_token_budget.py
    test_worker_manager_checkpoint.py
```

### 2.2 Test Classification

| Category | Files | Characteristics |
|----------|-------|-----------------|
| **Unit tests** | `test_*.py` (most) | Fast, no external dependencies, mocked I/O |
| **Integration tests** | `test_sandbox_integration.py` | Require `bwrap` binary; skipped via `pytestmark` |
| **Runtime tests** | `core/test_*_runtime*.py` | Test engine behavior with dummy clients and budget managers |
| **Tool tests** | `test_tools.py` | Exercise actual tool implementations on temp files |

---

## 3. Fixtures

### 3.1 Shared Fixtures (`tests/conftest.py`)

`conftest.py` defines a suite of dummy classes used across multiple test files. These are plain Python classes, not pytest fixtures (except `tmp_repo`):

| Class | Purpose |
|-------|---------|
| `DummyUsage` | Mock API usage object with token counts |
| `DummyTextBlock` | Mock text content block |
| `DummyToolUseBlock` | Mock tool_use content block |
| `DummyFinalMessage` | Mock final message with content + usage |
| `DummyStream` | Mock streaming context manager with `text_stream` iterator |
| `DummyClient` | Mock `LLMClient` with configurable stream queue |
| `DummyPermissionChecker` | Always-allow or configurable permission checker |
| `DummyReadOnlyTool` / `DummyWriteTool` | Minimal tool implementations for engine tests |
| `DummySessionStore` | In-memory message store |
| `DummyCostTracker` | In-memory usage tracker |

```python
@pytest.fixture
def tmp_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    notes = repo / "code-reading-notes"
    notes.mkdir()
    (notes / "manifest.json").write_text("{}", encoding="utf-8")
    return repo
```

### 3.2 Local Fixtures

Individual test files define their own fixtures for file system setup:

```python
@pytest.fixture
def tmp_file(tmp_path):
    f = tmp_path / "sample.txt"
    f.write_text("line one\nline two\nline three\n")
    return str(f)
```

### 3.3 Autouse Fixtures

The skill test file uses an `autouse` fixture to clear the global registry:

```python
@pytest.fixture(autouse=True)
def _clean_registry():
    clear_skills()
    yield
    clear_skills()
```

---

## 4. Mocking Patterns

### 4.1 unittest.mock

`unittest.mock` (MagicMock, patch, PropertyMock) is the primary mocking library.

#### Patching Object Methods

```python
def test_engine_returns_text_events():
    engine = _make_engine()
    with patch.object(engine._client, "stream_messages", return_value=_make_text_response("hello")):
        events = list(engine.submit("hi"))
    ...
```

#### Patching Module-Level Functions

```python
def test_build_system_prompt_includes_git_status_when_available():
    fake_result = MagicMock()
    fake_result.stdout = "main"
    with patch("core.context.subprocess.run", return_value=fake_result):
        prompt = build_system_prompt(cwd="/tmp")
    ...
```

#### Patching with side_effect

```python
with patch.object(engine._client, "stream_messages", side_effect=streams):
    events = list(engine.submit("use the echo tool"))
```

#### Patching Class Constructors

```python
@patch("core.main.EscListener", _FakeEscListener)
def test_run_query_prints_text(capsys):
    ...
```

### 4.2 pytest.MonkeyPatch

`monkeypatch` is used for environment variable and function replacement:

```python
def test_load_app_config_reads_anthropic_section(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env-key")
    ...
```

```python
def test_enabled_with_deps_ok(self, monkeypatch):
    monkeypatch.setattr(
        "core.sandbox.manager.check_dependencies",
        lambda: DependencyCheck(),
    )
    ...
```

### 4.3 Fake/Dummy Implementations

Rather than deep mocking, tests often create lightweight fake implementations:

```python
class _FakeEngine:
    def __init__(self, mode: str):
        self.mode = mode
        self.aborted = False
        self.prompts: list[str] = []

    def submit(self, prompt: str):
        self.prompts.append(prompt)
        if self.mode == "complete":
            yield ("text", f"finished:{prompt}")
            return
        ...

    def abort(self) -> None:
        self.aborted = True
```

```python
class _FakeEscListener:
    pressed = False
    def __init__(self, **kwargs): pass
    def __enter__(self): return self
    def __exit__(self, *_): pass
    def pause(self): pass
    def resume(self): pass
```

### 4.4 Temporary Files and Directories

`tmp_path` (pytest built-in) and `tmp_path_factory` are used for all file system tests:

```python
def test_file_edit_replaces_unique_string(tmp_path):
    f = tmp_path / "code.py"
    f.write_text("def hello():\n    pass\n")
    result = FileEditTool().execute(file_path=str(f), old_string="    pass", new_string='    return "hi"')
    assert not result.is_error
    assert 'return "hi"' in f.read_text()
```

---

## 5. Test Patterns by Subsystem

### 5.1 Engine Tests (`tests/test_engine.py`)

- Mock the `LLMClient.stream_messages` method to return fake streams.
- Verify event tuples: `("text", ...)`, `("tool_call", ...)`, `("tool_result", ...)`.
- Test tool execution loop, permission denial, unknown tools, and message normalization.
- Use `MagicMock` to simulate Anthropic SDK content blocks.

### 5.2 Tool Tests (`tests/test_tools.py`)

- Exercise real tool implementations against temporary files.
- Assert on `ToolResult.is_error` and `ToolResult.content`.
- Test edge cases: missing files, duplicate strings, timeouts, empty directories.

### 5.3 Config Tests (`tests/test_config.py`)

- Use `Namespace` to simulate CLI args.
- Use `monkeypatch` to control environment variables.
- Test priority: CLI > env > TOML file > defaults.
- Test validation: invalid `max_tokens`, invalid `effort` values.

### 5.4 LLM Tests (`tests/test_llm.py`)

- Test private normalization functions directly: `_to_openai_messages`, `_tool_schema_to_openai`.
- Verify round-trip conversion of tool_use / tool_result blocks between Anthropic and OpenAI formats.
- Test image input normalization.

### 5.5 Sandbox Tests

- **Unit tests** (`test_sandbox_manager.py`, `test_sandbox_wrapper.py`): Mock dependency checks and test configuration logic.
- **Integration tests** (`test_sandbox_integration.py`): Use `pytestmark` to skip when `bwrap` is unavailable:
  ```python
  pytestmark = pytest.mark.skipif(
      not shutil.which("bwrap"),
      reason="bwrap not available",
  )
  ```

### 5.6 Skill Tests (`tests/test_skills.py`)

- Organized into nested test classes by concern: `TestParseFrontmatter`, `TestSkill`, `TestRegistry`, `TestBundledSkills`, `TestLoadFromDisk`, `TestDiscoverSkills`, `TestPromptSection`, `TestAutocomplete`, `TestCommandParsing`.
- Use `autouse` fixture to isolate the global skill registry.

### 5.7 Cost Tracker Tests (`tests/test_cost_tracker.py`)

- Test private formatting helpers directly: `_fmt_tokens`, `_fmt_duration`, `_tier_for_model`.
- Test cost calculation with floating-point tolerance (`abs(cost - 18.0) < 0.001`).
- Test accumulation across multiple API calls and multiple models.

### 5.8 Runtime Budget Tests (`tests/core/test_engine_runtime_budget.py`)

- Use `DummyClient` and `DummyStream` from `conftest.py`.
- Monkeypatch `chdir` to control checkpoint output location.
- Test checkpoint triggering, artifact tracking, and post-tool budget checks.

---

## 6. Coverage Approach

### 6.1 What Is Tested

| Area | Coverage | Notes |
|------|----------|-------|
| Engine loop | High | Text events, tool execution, retries, normalization |
| Tool execution | High | All major tools tested with real temp files |
| Config loading | High | CLI, env, TOML, validation, defaults |
| LLM normalization | High | Anthropic/OpenAI round-trips |
| Permission system | High | Auto-approve, prompt, caching, plan mode |
| Cost tracking | High | Pricing tiers, formatting, accumulation |
| Skills | High | Parsing, registry, disk loading, bundled skills |
| Context builder | Medium | Sections, git status, CLAUDE.md inclusion |
| Sandbox (unit) | High | Config, manager, wrapper, checker |
| Sandbox (integration) | Conditional | Only when `bwrap` is available |
| Worker manager | Medium | Spawn, continue, stop, checkpoint detection |
| Coordinator | Medium | Mode switching, prompt generation |
| Dehydration | Medium | Message replacement, short-content skipping |
| Token budget | Medium | State transitions, estimation |
| Checkpoint | Medium | Manifest, progress, report writing |
| Companion/buddy | Medium | Storage, mood, companion logic |

### 6.2 What Is Not Extensively Tested

- The REPL UI layer (`main.py` rich console output) — tested via `capsys` and event inspection.
- Actual API calls to Anthropic/OpenAI — fully mocked.
- Threading race conditions in `WorkerManager` — basic spawn/stop coverage only.
- Wiki-strict subsystems (`src/core/wiki/`) — minimal test coverage.
- Knowledge system (`src/core/knowledge/`) — minimal test coverage.

### 6.3 CI Configuration

The project has minimal CI (`.github/workflows/wiki-lint.yml`) that runs wiki validation scripts, not pytest. Test execution is currently manual or run locally.

---

## 7. Test Style Guidelines

### 7.1 Assertions

- Prefer specific assertions over broad ones.
- Use `assert not result.is_error` for success checks on `ToolResult`.
- Use substring checks for error messages: `assert "not found" in result.content.lower()`.
- Use `pytest.raises(ValueError, match="...")` for expected exceptions.

### 7.2 Test Data

- Keep test data minimal and inline.
- Use string multiplication for large content: `"x" * 5000`.
- Use descriptive variable names: `tmp_path`, `tmp_repo`, `tmp_file`.

### 7.3 Test Isolation

- Each test should be independent.
- Use fixtures to set up and tear down shared state.
- Global state (skill registry) is reset via `autouse` fixtures.
- File system state is isolated via `tmp_path`.

### 7.4 Commented-Out Tests

Some test files contain commented-out tests (e.g., `tests/core/test_compact_runtime.py`, `tests/test_context.py`). These appear to be placeholders or tests disabled during refactoring.
