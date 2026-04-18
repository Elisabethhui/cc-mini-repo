# Codebase Concerns

**Analysis Date:** 2026-04-18

## Tech Debt

**Duplicate Function in `context.py`:**
- Issue: `_get_git_section()` is defined twice (lines 120-155 and 156-189) with identical bodies. The second definition shadows the first.
- Files: `src/core/context.py`
- Impact: Dead code, confusion for maintainers, risk of diverging implementations if only one copy is updated.
- Fix approach: Remove the duplicate definition.

**Stubbed Tree-Sitter Parser:**
- Issue: `_parse_with_tree_sitter()` in `ingester.py` returns a placeholder string instead of performing actual parsing.
- Files: `src/core/knowledge/ingester.py`
- Impact: Wiki ingestion for non-Python files falls back to basic text extraction, losing structural metadata.
- Fix approach: Implement tree-sitter integration or remove the stub and rely on the existing text fallback.

**Hardcoded `.cc-mini/` Paths Throughout Wiki Subsystems:**
- Issue: Multiple wiki modules reference `.cc-mini/` as a hardcoded workspace directory, but this directory was deleted during cleanup.
- Files: `src/core/wiki/taskpack.py`, `src/core/wiki/post_edit_guard.py`, `src/core/wiki/reconcile.py`, `src/core/wiki/archive.py`, `src/core/wiki/maintenance.py`, `src/core/tools/file_edit_strict.py`
- Impact: Any wiki-strict mode operation that writes to or reads from `.cc-mini/` will fail with `FileNotFoundError`.
- Fix approach: Centralize workspace path configuration in `config.py` and make all wiki modules read from config.

**Companion/Poke Game Direct Terminal Manipulation:**
- Issue: The idle adventure game uses raw ANSI escape sequences and `tty.setcbreak` to manipulate the terminal directly.
- Files: `src/core/buddy/poke_game/loop.py`, `src/core/buddy/poke_game/render.py`, `src/core/_keylistener.py`
- Impact: Terminal state corruption if the process crashes or is interrupted; incompatible with non-TTY environments (CI, IDEs, Windows without proper handling).
- Fix approach: Use a proper TUI library (e.g., `rich`, `blessed`) or isolate the game in a subprocess.

**Companion Animator Daemon Thread Without Cleanup:**
- Issue: `animator.py` starts a daemon thread for animation updates but lacks a clean shutdown mechanism.
- Files: `src/core/buddy/animator.py`
- Impact: Thread may leak or leave the terminal in an inconsistent state on exit.
- Fix approach: Add a `stop()` method with an `Event` flag and ensure it is called during REPL shutdown.

**Post-Edit Guard Missing `async def` Handling:**
- Issue: `_extract_ast_symbols()` only checks for `ast.ClassDef` and `ast.FunctionDef`, missing `ast.AsyncFunctionDef`.
- Files: `src/core/wiki/post_edit_guard.py`
- Impact: Async functions are invisible to the post-edit impact analysis, causing false negatives in change detection.
- Fix approach: Add `ast.AsyncFunctionDef` to the visitor.

**Demo/Mock Code in Production Commands:**
- Issue: `_cmd_post_edit` in `commands.py` contains hardcoded demo patch analysis with mock content.
- Files: `src/core/commands.py`
- Impact: The `/post_edit` command does not perform real analysis in production; it returns canned results.
- Fix approach: Replace the hardcoded demo with a call to the actual `PostEditGuard` implementation.

## Known Bugs

**Shell Injection in `_run_shell`:**
- Symptoms: Arbitrary command execution via unsanitized input passed to `subprocess.run(cmd, shell=True, ...)`.
- Files: `src/core/main.py` (line ~1360), `src/core/tools/bash.py` (line ~70)
- Trigger: Any tool or command that constructs a shell command from user input or LLM output.
- Workaround: None. The `SandboxManager` wraps commands but is not always enabled.

**Shell Injection in `BashTool`:**
- Symptoms: Same as above; `BashTool.execute()` passes `command` directly to `subprocess.run` with `shell=True`.
- Files: `src/core/tools/bash.py`
- Trigger: LLM generates a malicious `command` parameter.
- Workaround: Enable sandbox mode (`bwrap`) for untrusted commands.

**Race Condition in Wiki Watcher:**
- Symptoms: File watcher thread may miss rapid successive changes or crash on directory deletion.
- Files: `src/core/knowledge/watcher.py`
- Trigger: Rapid file modifications during `ingest_all()` or concurrent edits.
- Workaround: Restart the watcher manually.

**Companion Game Terminal State Leak:**
- Symptoms: After exiting the companion game, the terminal may not restore echo or canonical mode.
- Files: `src/core/buddy/poke_game/loop.py`, `src/core/_keylistener.py`
- Trigger: SIGINT or unhandled exception during game loop.
- Workaround: Run `reset` in the terminal.

## Security Considerations

**Arbitrary Code Execution via `shell=True`:**
- Risk: Critical. Multiple locations use `shell=True` with unsanitized input.
- Files: `src/core/main.py`, `src/core/tools/bash.py`
- Current mitigation: `SandboxManager` with bubblewrap is available but opt-in.
- Recommendations: Disable `shell=True` by default; parse commands into lists and use `shell=False`. Make sandbox mode mandatory for write tools.

**API Key Exposure via `load_dotenv()` at Module Level:**
- Risk: Environment variables are loaded at import time, making it easy to accidentally log or leak them.
- Files: `src/core/config.py`
- Current mitigation: Keys are stored in `.env` files which are typically `.gitignore`d.
- Recommendations: Load dotenv explicitly in `main()` rather than at module import time. Validate that `.env` is in `.gitignore`.

**File Path Traversal in File Tools:**
- Risk: `FileReadTool`, `FileEditTool`, `FileWriteTool`, and `GlobTool` accept arbitrary `file_path` parameters without path validation.
- Files: `src/core/tools/file_read.py`, `src/core/tools/file_edit.py`, `src/core/tools/file_write.py`, `src/core/tools/glob_tool.py`
- Current mitigation: None. The permission system prompts for write tools but does not validate paths.
- Recommendations: Add a path sandbox that restricts file operations to the project root or a configured allow-list.

**Unvalidated Regex in `GrepTool`:**
- Risk: Malformed regex patterns can cause `re.error` or ReDoS (Regular Expression Denial of Service) on large files.
- Files: `src/core/tools/grep_tool.py`
- Current mitigation: None.
- Recommendations: Wrap regex compilation in a try/except and set a timeout or complexity limit.

## Performance Bottlenecks

**Token Estimation Heuristic:**
- Problem: `estimate_from_messages()` divides total characters by 1.8, which is a coarse approximation.
- Files: `src/core/token_budget.py`
- Cause: No actual tokenizer is used; the heuristic can be off by 30-50% for code or non-English text.
- Improvement path: Integrate `tiktoken` or the Anthropic tokenizer for accurate token counts.

**Synchronous File I/O in Tool Execution:**
- Problem: File read/edit/write tools perform blocking I/O on the main thread.
- Files: `src/core/tools/file_read.py`, `src/core/tools/file_edit.py`, `src/core/tools/file_write.py`
- Cause: Python's default file operations are synchronous.
- Improvement path: Use `aiofiles` or move I/O to a thread pool if the engine becomes async.

**Companion Game Busy-Wait Loop:**
- Problem: The auto-adventure thread in `poke_game/loop.py` uses `time.sleep(0.1)` in a tight loop.
- Files: `src/core/buddy/poke_game/loop.py`
- Cause: Inefficient polling for state updates.
- Improvement path: Use an `Event` or `Condition` variable to wake the thread only when needed.

**Large Message Lists Without Pagination:**
- Problem: The engine passes the entire conversation history to the LLM on every turn.
- Files: `src/core/engine.py`
- Cause: No message windowing or summarization beyond the compact/checkpoint triggers.
- Improvement path: Implement sliding window context management with smarter retention of system/tool messages.

## Fragile Areas

**Token Budget Decision Logic:**
- Files: `src/core/engine.py`, `src/core/token_budget.py`
- Why fragile: The pre-flight token estimate is multiplied by 1.5 as a safety factor, then passed to `BudgetManager.decide()`. If the heuristic is wrong, the engine may checkpoint too early or exceed limits.
- Safe modification: Add unit tests with known token counts and verify boundary behavior.
- Test coverage: Limited. `test_engine.py` mocks the client but does not test budget decisions.

**Wiki Reconciliation (`reconcile.py`):**
- Files: `src/core/wiki/reconcile.py`
- Why fragile: Relies on file timestamps and frontmatter hashes to detect stale entities. Clock skew or hash collisions can cause false positives/negatives.
- Safe modification: Add a dry-run mode and logging for reconciliation decisions.
- Test coverage: No dedicated tests found.

**Flow State Machine (`flow_state.py`):**
- Files: `src/core/flow_state.py`
- Why fragile: State transitions are string-based and scattered across `commands.py` and `engine.py`. A typo in a state name causes silent failures.
- Safe modification: Use the `FlowState` enum everywhere and add exhaustive transition validation.
- Test coverage: Minimal.

**AST-Based Code Reading (`ast_read.py`):**
- Files: `src/core/tools/ast_read.py`
- Why fragile: Uses the Python `ast` module, which is version-sensitive. Code using Python 3.12+ syntax may fail to parse on older interpreters.
- Safe modification: Catch `SyntaxError` and fall back to text reading.
- Test coverage: Basic tests exist but do not cover edge cases like walrus operators or pattern matching.

**Drift Tracker (`ingester.py`):**
- Files: `src/core/knowledge/ingester.py`
- Why fragile: `MAX_RETRY = 3` with no backoff or jitter. Rapid retries can overwhelm the file system or race with external editors.
- Safe modification: Add exponential backoff and a maximum total retry duration.
- Test coverage: None.

## Scaling Limits

**SQLite Session Store:**
- Current capacity: Single-file SQLite database.
- Limit: Concurrent writes from multiple `cc-mini` instances will cause `database is locked` errors.
- Scaling path: Use WAL mode or switch to a server-based database if multi-instance support is needed.

**Companion Storage (JSON File):**
- Current capacity: Single JSON file per companion.
- Limit: Large adventure logs or many companions will cause slow load/save times and memory bloat.
- Scaling path: Switch to SQLite or a key-value store for companion state.

**ThreadPoolExecutor for Read-Only Tools:**
- Current capacity: Default `max_workers` (typically CPU count * 5).
- Limit: If many read-only tools are dispatched concurrently, the executor may saturate.
- Scaling path: Make `max_workers` configurable and add a semaphore for concurrent tool execution.

## Dependencies at Risk

**`prompt_toolkit` (REPL Dependency):**
- Risk: The entire REPL and slash command autocomplete depend on `prompt_toolkit`.
- Impact: If `prompt_toolkit` introduces breaking changes or becomes unmaintained, the CLI experience degrades.
- Migration plan: Pin to a known-good version and monitor for alternatives like `rich` + `click`.

**Anthropic SDK (`anthropic`):**
- Risk: The `LLMClient` wraps the Anthropic SDK directly. API changes or deprecation of streaming methods will break the engine.
- Impact: Complete loss of LLM functionality for Anthropic models.
- Migration plan: Maintain a thin abstraction layer (`LLMClient`) and test against SDK beta releases.

## Missing Critical Features

**No Input Validation on Tool Schemas:**
- Problem: Tool `input_schema` is passed to the LLM but not validated on the Python side before `execute()` is called.
- Blocks: Safe tool execution. Malformed or missing parameters cause `TypeError` or `KeyError` at runtime.
- Priority: High.

**No Rate Limiting or Retry Budget for LLM Calls:**
- Problem: `LLMClient` has retry logic but no global rate-limit budget or circuit breaker.
- Blocks: Resilience against API outages or rate limits.
- Priority: Medium.

**No Audit Log for Tool Executions:**
- Problem: Tool results are streamed to the user but not persisted to an immutable audit log.
- Blocks: Forensic analysis of what the AI did, especially for write tools.
- Priority: Medium.

## Test Coverage Gaps

**Wiki Subsystems Untested:**
- What's not tested: `taskpack.py`, `reconcile.py`, `archive.py`, `maintenance.py`, `post_edit_guard.py`, `lint.py`, `target_identity.py`.
- Files: `src/core/wiki/*.py`
- Risk: Wiki-strict mode regressions go unnoticed.
- Priority: High.

**Companion System Untested:**
- What's not tested: `animator.py`, `poke_game/*`, `storage.py`, `_keylistener.py`.
- Files: `src/core/buddy/*.py`, `src/core/_keylistener.py`
- Risk: Terminal corruption or game state bugs.
- Priority: Medium.

**Configuration Loading Untested:**
- What's not tested: TOML parsing, environment variable precedence, model alias resolution.
- Files: `src/core/config.py`
- Risk: Config changes break startup silently.
- Priority: Medium.

**Error Handler and Recovery Untested:**
- What's not tested: `error_handler.py`, retry logic in `llm.py`, checkpointing in `engine.py`.
- Files: `src/core/tools/error_handler.py`, `src/core/llm.py`, `src/core/engine.py`
- Risk: API errors cause crashes instead of graceful degradation.
- Priority: High.

---

*Concerns audit: 2026-04-18*
