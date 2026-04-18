# cc-mini Codebase Concerns

> Generated: 2026-04-18
> Scope: src/core/ (26,257 lines), tests/ (3,057 lines), and related subsystems

---

## Table of Contents

1. [Security Issues](#1-security-issues)
2. [Performance Concerns](#2-performance-concerns)
3. [Code Quality Issues](#3-code-quality-issues)
4. [Testing Gaps](#4-testing-gaps)
5. [Architecture Concerns](#5-architecture-concerns)
6. [Maintenance Challenges](#6-maintenance-challenges)

---

## 1. Security Issues

### 1.1 Bash Tool: `shell=True` with unsanitized input
**File:** `src/core/tools/bash.py` (lines 92-95)

```python
result = subprocess.run(
    actual_command, shell=True, capture_output=True,
    text=True, encoding="utf-8", errors="replace", timeout=timeout,
)
```

- **Risk:** Even with sandboxing, `shell=True` passes commands through `/bin/sh`. If sandboxing is disabled or bypassed, command injection is possible. The `actual_command` can be user-controlled via the LLM's tool call.
- **Mitigation:** The sandbox wrapper (`src/core/sandbox/wrapper.py`) wraps commands in `bwrap`, but if `dangerously_disable_sandbox=True` is passed and config allows it, the raw command runs unsandboxed.

### 1.2 Sandbox bypass via `dangerously_disable_sandbox`
**File:** `src/core/tools/bash.py` (line 81), `src/core/sandbox/manager.py` (lines 60-75)

- The `dangerously_disable_sandbox` parameter in `BashTool.execute()` allows explicit sandbox disabling. The `SandboxManager.should_sandbox()` checks `self._config.allow_unsandboxed`, but this is a config flag that could be set to `True` by a compromised or misconfigured `.cc-mini.toml`.
- **Risk:** A malicious or confused LLM could pass `dangerously_disable_sandbox=true` on sensitive commands.

### 1.3 API keys in environment and config files
**File:** `src/core/config.py` (lines 279-286, 333-342)

- API keys are read from environment variables (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) and TOML config files. There is no keyring integration, no encryption at rest, and no masking in logs.
- **Risk:** Keys may be exposed in process listings (`ps e`), shell history, or accidentally committed config files.

### 1.4 File Edit/Write tools lack path traversal validation
**File:** `src/core/tools/file_edit.py`, `src/core/tools/file_write.py`

- `FileEditTool` and `FileWriteTool` accept absolute paths but do not validate against directory traversal (`../../etc/passwd`). While the REPL runs as the user, an LLM could be tricked into overwriting sensitive files.
- **Risk:** Overwriting `~/.bashrc`, `/etc/hosts`, or other critical files if the model is manipulated.

### 1.5 Session data stored in plaintext JSONL
**File:** `src/core/session.py` (lines 22, 120-158)

- Sessions are stored in `~/.mini-claude/sessions/{sanitized_cwd}/` as plaintext JSONL files. No encryption, no access control beyond filesystem permissions.
- **Risk:** Conversation history (which may contain sensitive code, secrets, or PII) is stored unencrypted.

### 1.6 Companion observer swallows all exceptions silently
**File:** `src/core/buddy/observer.py` (lines 151-152)

```python
except Exception:
    pass  # Non-essential — silently swallow all errors
```

- The companion observer runs in a background thread and silently catches all exceptions. This could mask security-relevant failures (e.g., network exfiltration attempts via the companion LLM call).

### 1.7 Sandbox wrapper: `--ro-bind / /` grants read access to entire filesystem
**File:** `src/core/sandbox/wrapper.py` (line 43)

```python
args.extend(["--ro-bind", "/", "/"])  # Global read-only
```

- The sandbox mounts the entire root filesystem as read-only. While this prevents writes, it exposes all files readable by the user (SSH keys, `.env` files, browser cookies, etc.) to any command running in the sandbox.
- **Risk:** A malicious or compromised LLM could read sensitive files via sandboxed commands.

### 1.8 No input validation on image file paths in `_parse_input`
**File:** `src/core/main.py` (lines 368-399)

- The `@path` image reference parser reads files directly without validating that the path is within the project directory or safe. Symlinks could be exploited.

---

## 2. Performance Concerns

### 2.1 Token estimation is crude and potentially inaccurate
**File:** `src/core/token_budget.py` (lines 45-52)

```python
def estimate_from_messages(self, messages: list[dict[str, Any]]) -> int:
    total_chars = 0
    for msg in messages:
        total_chars += self._count_message_chars(msg)
    estimate = max(1, int(total_chars / 1.8))
```

- Uses a hardcoded `1.8` chars-per-token ratio. This is inaccurate for code (which has many short tokens) and non-English text. The comment even suggests `// 1.5` or `// 2` but it was never changed.
- **Impact:** Could trigger premature dehydration/compaction or miss actual OOM conditions.

### 2.2 Engine loop performs multiple token estimates per turn
**File:** `src/core/engine.py` (lines 262-313, 420-434)

- The `submit()` method runs token estimation, dehydration, compaction, and checkpoint logic both before AND after the API call. Each `estimate_from_messages()` iterates over all messages and counts characters.
- **Impact:** O(n) per turn where n = message count. For long sessions this adds up, though not severely.

### 2.3 Wiki ingester blocks the main thread on startup
**File:** `src/core/main.py` (lines 1044-1052)

```python
if run_mode == RunMode.WIKI_STRICT:
    ingester = WikiIngester(cwd)
    ingester.ingest_all()  # 阻塞式首次扫描
```

- In `WIKI_STRICT` mode, the entire workspace is scanned and AST-parsed before the REPL starts. On large codebases this could take seconds.
- **Impact:** Startup latency; no progress indicator; blocks user interaction.

### 2.4 File watcher triggers full re-ingestion on every file change
**File:** `src/core/knowledge/watcher.py` (lines 68-84)

```python
def _handle_change(self, file_path: str):
    # ...
    self.ingester.ingest_file(path)
    self.ingester.ingest_all()  # 全量重建 L1 index
```

- Every file modification triggers a full `ingest_all()` rebuild of the L1 index. The comment says "耗时极短" but this is O(n) over the entire workspace.
- **Impact:** High CPU/disk usage during active editing sessions.

### 2.5 Glob tool sorts by mtime using stat() on every match
**File:** `src/core/tools/glob_tool.py` (lines 39-40)

```python
matches = glob_module.glob(pattern, root_dir=str(base), recursive=True)
matches = sorted(matches, key=lambda p: (base / p).stat().st_mtime, reverse=True)
```

- `stat()` is called for every matched file. For large glob results (e.g., `**/*.py` in a big repo), this is expensive.
- **Impact:** Slow glob operations on large repositories.

### 2.6 Companion observer makes synchronous API calls in background thread
**File:** `src/core/buddy/observer.py` (lines 117-127, 135-150)

- The companion observer spawns a daemon thread that makes blocking `LLMClient.create_message()` calls. While this doesn't block the main thread, it consumes API tokens and network bandwidth for a non-essential feature.
- **Impact:** Unnecessary API usage; could contribute to rate limiting.

### 2.7 No caching for AST parsing in TargetResolver
**File:** `src/core/wiki/target_identity.py` (lines 166-171, 213-246)

- `TargetResolver._compute_content_hash()` and `_extract_symbols_from_file()` re-read and re-parse files on every `/prime` call. No caching of AST results.
- **Impact:** Repeated parsing of the same files.

---

## 3. Code Quality Issues

### 3.1 Duplicate `_get_git_section()` function
**File:** `src/core/context.py` (lines 123-155, 157-189)

- The entire `_get_git_section()` function is defined twice with identical bodies. This is clearly a copy-paste error.

### 3.2 TODO comments indicating incomplete features
**File:** `src/core/tools/file_edit_strict.py` (line 132)
```python
# TODO: 这里可以接入更高级的模糊替换算法，此处演示强行接管
```

**File:** `src/core/knowledge/ingester.py` (line 329)
```python
# TODO: 接入 tree-sitter 逻辑
```

- Tree-sitter integration is stubbed out; JS/TS/Java files get placeholder summaries.
- The fuzzy replacement in `file_edit_strict.py` falls back to a manual prompt instead of an algorithm.

### 3.3 Mixed languages in codebase (Chinese + English)
- Many modules have Chinese comments, variable names, and docstrings mixed with English. Examples:
  - `src/core/wiki/taskpack.py` — Chinese docstrings for dataclasses
  - `src/core/engine.py` — Chinese comments for token budget logic
  - `src/core/knowledge/ingester.py` — Chinese print statements and comments
- **Impact:** Inconsistent codebase; harder for non-Chinese-speaking contributors to maintain.

### 3.4 `get_minimal_goal_stack()` is a stub returning empty strings
**File:** `src/core/coordinator.py` (lines 318-340)

```python
def get_minimal_goal_stack() -> dict[str, str]:
    """Phase 1 占位函数：返回最小 Goal Stack 结构。"""
    return {
        "global_goal": "",
        "step_goal": "",
        ...
    }
```

- Documented as a placeholder ("占位函数") but still shipped and referenced. No actual goal stack orchestration is implemented.

### 3.5 `PlanModeManager.enter()` creates new tool instances instead of reusing
**File:** `src/core/plan.py` (lines 122-131)

- Every time plan mode is entered, fresh tool instances are created. This loses any stateful tool instances (e.g., `FileEditTool_S` fail counts, backup tracking).

### 3.6 `engine.py` uses bare `print()` for token risk alerts
**File:** `src/core/engine.py` (lines 268, 282, 284)

```python
print(f"[Token Risk] state={decision.state.value}, tokens={decision.token_estimate}")
```

- Should use the Rich console for consistent output formatting, not bare `print()`.

### 3.7 `CheckpointManager` writes to `code-reading-notes/` in the repo
**File:** `src/core/checkpoint.py` (lines 24-29)

- Checkpoints are written to `{repo_root}/code-reading-notes/` which is inside the git repository. This could create untracked files that accidentally get committed.

### 3.8 `FileEditTool_S` (strict) has different class name than standard `FileEditTool`
**File:** `src/core/tools/file_edit_strict.py` (line 13)

```python
class FileEditTool(Tool):
```

- Both `file_edit.py` and `file_edit_strict.py` define a class named `FileEditTool`. This is confusing and relies on import aliasing (`FileEditTool_S`) in `main.py` to disambiguate.

### 3.9 `Memory.py` has duplicate session persistence logic
**File:** `src/core/memory.py` (lines 336-372)

- `save_session()` and `load_session()` duplicate functionality already present in `src/core/session.py` (`SessionStore`). The memory module's session functions use a different directory (`~/.mini-claude/sessions/` vs `SessionStore`'s same path) but similar JSONL format.

### 3.10 `context.py` has unused import and stray code
**File:** `src/core/context.py` (lines 312-313)

```python
from pathlib import Path
```

- This import appears at the end of the file, after the `build_system_prompt()` function, and is never used.

---

## 4. Testing Gaps

### 4.1 No tests for `WIKI_STRICT` mode
- The entire wiki-strict subsystem (`src/core/wiki/`, `src/core/knowledge/`, `src/core/tools/ast_read.py`, `src/core/tools/file_edit_strict.py`) has zero test coverage.
- **Missing:**
  - `ASTReadTool` symbol/span/anchor resolution
  - `FileEditTool_S` backup, rollback, preview, fuzzy fallback
  - `WikiIngester` AST parsing and frontmatter handling
  - `TokenBudgetManager` threshold decisions
  - `CheckpointManager` persistence
  - `PostEditGuard` impact analysis
  - `TargetResolver` disambiguation logic

### 4.2 No tests for the companion/buddy subsystem
**Files:** `src/core/buddy/*.py`, `src/core/buddy/poke_game/*.py`

- The companion system, mood tracking, idle adventure game, and poke game have no tests. This is ~2,500+ lines of untested code.

### 4.3 No tests for `PlanModeManager`
**File:** `src/core/plan.py`

- Plan mode enter/exit, tool restriction, prompt injection, and file creation are untested.

### 4.4 No tests for `CompactService`
**File:** `src/core/compact.py`

- The context compression logic (message splitting, media stripping, alternation fixing) has no unit tests. Only `estimate_tokens()` is indirectly tested via `test_engine.py`.

### 4.5 No tests for `CostTracker`
**File:** `src/core/cost_tracker.py`

- While there is a `test_cost_tracker.py`, it only tests formatting helpers (`_fmt_tokens`, `_fmt_duration`). The actual `CostTracker.add_usage()`, `calculate_cost()`, and model pricing lookup are not tested.

### 4.6 Sandbox integration tests are skipped if bwrap unavailable
**File:** `tests/test_sandbox_integration.py`

```python
pytestmark = pytest.mark.skipif(not shutil.which("bwrap"), reason="bwrap not available")
```

- CI environments (macOS, Windows) will skip these tests entirely. No mock-based tests exist for sandbox logic on non-Linux platforms.

### 4.7 No tests for error handling and retry loops
**File:** `src/core/tools/error_handler.py`, `src/core/tools/reanchor.py`

- `RetryLoop`, `verify_and_retry()`, `ReanchorLoop`, and `execute_with_reanchor()` have no tests.

### 4.8 No tests for `WorkerManager` task lifecycle edge cases
**File:** `tests/test_worker_manager.py`

- Tests exist for spawn/continue/stop but miss:
  - Concurrent task spawning
  - Notification queue overflow
  - Task ID collision (unlikely but possible with 8-char hex)
  - Engine failure mid-task

### 4.9 No tests for permission prompt interaction
**File:** `src/core/permissions.py`

- The `_prompt_user()` method reads from `sys.stdin` directly. There are no integration tests for the actual interactive prompt flow (only mocked tests in `test_permissions.py`).

### 4.10 No tests for `SessionStore` edge cases
**File:** `src/core/session.py`

- Missing tests for:
  - Corrupted JSONL lines (line 177: `except json.JSONDecodeError: continue`)
  - Very long CWD paths (>80 chars sanitization)
  - Concurrent session writes
  - Session metadata corruption recovery

---

## 5. Architecture Concerns

### 5.1 Circular import risk between `engine.py` and `compact.py`
**File:** `src/core/engine.py` (line 6), `src/core/compact.py` (line 9)

- `engine.py` imports `CompactService` from `compact.py`. `compact.py` imports `LLMClient` from `llm.py`. While not a direct circular import, the tight coupling means the engine cannot function without the compaction subsystem.

### 5.2 `Engine` class is a God Object
**File:** `src/core/engine.py` (lines 99-611)

- The `Engine` class handles: API streaming, retry logic, tool execution, permission checking, message normalization, token budgeting, checkpointing, cost tracking, dehydration, and compaction. It is ~500 lines and violates single responsibility.
- **Refactor candidates:** Extract `ToolExecutor`, `MessageNormalizer`, `TokenBudgetController`.

### 5.3 Global skill registry (`_REGISTRY`)
**File:** `src/core/skills.py` (line 154)

```python
_REGISTRY: dict[str, Skill] = {}
```

- The skill registry is a module-level global mutable dict. This makes testing difficult (requires `clear_skills()` between tests) and prevents multiple concurrent `Engine` instances from having different skill sets.

### 5.4 `main.py` is excessively large (1,394 lines)
**File:** `src/core/main.py`

- Contains: CLI parsing, REPL loop, prompt rendering, streaming markdown, spinner management, command dispatch, sandbox command handling, companion integration, auto-dream logic, and wiki-strict mode initialization.
- **Refactor candidates:** Extract `REPL`, `PromptRenderer`, `EventLoop`, `CompanionIntegration` into separate modules.

### 5.5 Wiki-strict mode adds significant complexity with unclear benefits
- The wiki-strict subsystem (`src/core/wiki/`, `src/core/knowledge/`) adds ~3,500 lines of code for a mode that is opt-in and not well-tested.
- Many wiki modules (`archive.py`, `query_archive.py`, `maintenance.py`, `lint.py`) are essentially standalone utilities that duplicate functionality (file age checking, JSON manifest management) that could be handled by simpler scripts.

### 5.6 `ReconcileEngine` has a stub `RE_DIGEST` action
**File:** `src/core/wiki/reconcile.py` (lines 225-228)

```python
elif action == ReconcileAction.RE_DIGEST:
    result["message"] = f"Re-digest triggered for {entity_path}"
    result["applied"] = True
```

- The `RE_DIGEST` action is a no-op — it just returns a message. The actual re-digest logic is not implemented.

### 5.7 `MaintenanceEngine.stale_recovery()` is also a stub
**File:** `src/core/wiki/maintenance.py` (lines 274-304)

- `stale_recovery()` checks for `status: stale` but the actual recovery logic is commented out / not implemented ("Would trigger re-digest here").

### 5.8 `get_flow_state_prompt()` hardcodes a 4-state machine in a string
**File:** `src/core/flow_state.py` (lines 10-39)

- The entire wiki-strict state machine is a single multiline string. No validation, no state transition enforcement in code, just a prompt injection.

### 5.9 `BashTool` and `GrepTool` both shell out to external binaries
**File:** `src/core/tools/bash.py`, `src/core/tools/grep_tool.py`

- `BashTool` relies on `/bin/sh`. `GrepTool` relies on `rg` (ripgrep) with a Python fallback. These external dependencies are not declared in `pyproject.toml` and may not be available.

### 5.10 `EscListener` has platform-specific implementations in one file
**File:** `src/core/_keylistener.py`

- The Unix (`termios/tty`) and Windows (`msvcrt`) implementations are in the same file with conditional class redefinition. This is hard to test and maintain.

---

## 6. Maintenance Challenges

### 6.1 Hardcoded constants scattered throughout
| Constant | Location | Context |
|----------|----------|---------|
| `8000` (MAX_TOOL_OUTPUT_CHARS) | `src/core/engine.py:560` | Tool output truncation |
| `120` (Bash timeout default) | `src/core/tools/bash.py:11` | Command timeout |
| `30` (Grep timeout) | `src/core/tools/grep_tool.py:66` | Search timeout |
| `2000` (File read limit) | `src/core/tools/file_read.py:28` | Max lines to read |
| `10` (max workers) | `src/core/engine.py:476` | ThreadPoolExecutor |
| `1.8` (chars/token) | `src/core/token_budget.py:50` | Token estimation |
| `32000` (32K context) | `src/core/token_budget.py:23` | Hard stop limit |
| `7` days (snapshot age) | `src/core/wiki/maintenance.py:42` | Archive threshold |
| `24.0` hours (dream interval) | `src/core/config.py:86` | Auto-dream interval |
| `5` (min sessions) | `src/core/config.py:87` | Auto-dream gate |

### 6.2 No centralized configuration schema
- Config values are spread across `config.py`, `sandbox/config.py`, `memory.py`, `token_budget.py`, and inline in `main.py`. There is no single source of truth for defaults.

### 6.3 `pyproject.toml` / dependencies not audited
- The `openai` package is imported with a broad `except Exception` catch (line 16 of `llm.py`). If `openai` is installed but incompatible, the error is silently stored and only surfaced when OpenAI provider is selected.

### 6.4 Wiki entity frontmatter parsing is ad-hoc
**File:** `src/core/knowledge/ingester.py` (lines 128-158)

- Frontmatter is parsed with a custom regex and string splitting, not a proper YAML parser. This will break on multi-line values, nested structures, or YAML-specific syntax.

### 6.5 `QueryArchive` relies on a JSON manifest that is never updated by `ArchiveEngine`
**File:** `src/core/wiki/archive.py`, `src/core/wiki/query_archive.py`

- `ArchiveEngine.archive_item()` calls `_update_manifest()`, but `auto_archive()` does NOT update the manifest for dry-run items. The manifest can become inconsistent.

### 6.6 `PostEditGuard` uses `ast.parse()` on potentially invalid Python
**File:** `src/core/wiki/post_edit_guard.py` (lines 224-275)

- `ast.parse()` is called on the original content. If the file had a syntax error before the edit, the guard silently falls back to line-count comparison, losing semantic analysis.

### 6.7 `FileEditTool_S` backups accumulate without cleanup
**File:** `src/core/tools/file_edit_strict.py` (lines 46-55)

- Backups are stored in `.cc-mini/backups/` with timestamps. There is no cleanup mechanism — old backups will accumulate indefinitely.

### 6.8 `DriftTracker` drift log is never pruned
**File:** `src/core/knowledge/ingester.py` (lines 21-47)

- The `drift_log.json` records failures per path. Successful paths are removed, but if a path permanently fails 3+ times, it stays in the log forever.

### 6.9 `CompanionChat` history is never persisted
**File:** `src/core/buddy/observer.py` (lines 35-58)

- Module-level `_companion_chat` stores conversation history in memory. It is lost when the process exits and grows unbounded up to `_MAX_CHAT_HISTORY = 20`.

### 6.10 `test_sandbox_integration.py` uses `shell=True` in tests
**File:** `tests/test_sandbox_integration.py` (lines 25, 77, 101)

- The test helper `_run_sandboxed()` uses `shell=True` to execute the already-wrapped sandbox command. This is a test anti-pattern that could mask real issues.

---

## Summary Statistics

| Category | Count | Severity |
|----------|-------|----------|
| Security issues | 8 | High: 4, Medium: 3, Low: 1 |
| Performance concerns | 7 | High: 2, Medium: 4, Low: 1 |
| Code quality issues | 10 | High: 1, Medium: 6, Low: 3 |
| Testing gaps | 10 | High: 5, Medium: 4, Low: 1 |
| Architecture concerns | 10 | High: 3, Medium: 5, Low: 2 |
| Maintenance challenges | 10 | High: 2, Medium: 5, Low: 3 |
| **Total** | **55** | **High: 17, Medium: 27, Low: 11** |

---

## Recommendations (Priority Order)

1. **Immediate (Security):**
   - Remove or restrict `dangerously_disable_sandbox` parameter
   - Add path traversal validation to FileEditTool and FileWriteTool
   - Encrypt or protect session JSONL files
   - Restrict sandbox read-only mount to project directory only

2. **Short-term (Stability):**
   - Remove duplicate `_get_git_section()` in `context.py`
   - Add tests for wiki-strict mode core paths
   - Fix `FileEditTool_S` class name collision
   - Add proper exception logging in companion observer

3. **Medium-term (Architecture):**
   - Refactor `Engine` into smaller focused classes
   - Extract REPL logic from `main.py`
   - Replace ad-hoc frontmatter parsing with a proper parser
   - Consolidate configuration defaults

4. **Long-term (Quality):**
   - Achieve >80% test coverage for `src/core/wiki/` and `src/core/knowledge/`
   - Remove or implement stub functions (`get_minimal_goal_stack`, `RE_DIGEST`, `stale_recovery`)
   - Add cleanup mechanisms for backups and drift logs
   - Internationalize or standardize on English for all code comments
