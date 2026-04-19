# Domain Pitfalls: Context Management for AI Coding Assistants

**Domain:** AI coding assistant with 32K token context support
**Researched:** 2026-04-20
**Confidence:** HIGH (based on codebase analysis + industry research + production bug reports)

## Critical Pitfalls

Mistakes that cause rewrites, data loss, or security incidents.

### Pitfall 1: Heuristic Token Counting Without Ground Truth Calibration

**What goes wrong:** The token estimator uses `total_chars / 1.8` (in `token_budget.py`), which can be off by 30-50% for code or non-English text. The engine then multiplies this by 1.5 as a "safety factor," creating a compounding error of up to 2x. This causes either premature checkpointing (wasting context) or silent overruns (hitting API limits).

**Why it happens:**
- Code tokenizes at ~2-3 chars/token (not 1.8)
- URLs/paths tokenize at ~1 char per slash/dot
- CJK text tokenizes at ~1-2 chars/token
- The `1.5x` multiplier in `engine.py` line 263 is a band-aid, not a fix

**Consequences:**
- Session halts prematurely when plenty of context remains
- API calls fail with `ContextWindowExceededError` when the heuristic underestimated
- The `TokenBudgetManager` enters `HARD_STOP` or `CHECKPOINT` state incorrectly
- User loses work due to unnecessary checkpoint triggers

**Prevention:**
1. Integrate `tiktoken` (for OpenAI) or `anthropic` tokenizer (for Claude) for accurate counts
2. Use API-reported `usage.input_tokens` as ground truth after every call
3. Maintain a running calibration factor: `actual / estimated` per call
4. Remove the `1.5x` multiplier; replace with calibrated estimation

**Detection:**
- Log `estimated` vs `actual` tokens on every API call
- Alert when error exceeds 10% for 3 consecutive calls
- Monitor for "phantom checkpoints" (checkpoints triggered when usage is well below limit)

**Phase to address:** Phase 1 (Token Budget Foundation)

---

### Pitfall 2: Compaction Hangs and Infinite Loops

**What goes wrong:** The `CompactService.compact()` method calls the LLM to summarize conversation history. If the summary itself exceeds `COMPACT_MAX_OUTPUT_TOKENS` (4096), or if the model hangs, the entire engine blocks indefinitely. There is no timeout on the compaction call itself, and no fallback to truncation.

**Why it happens:**
- `CompactService.compact()` calls `self._client.create_message()` without a timeout parameter
- The compact prompt (`COMPACT_PROMPT`) is ~1.5K tokens; with history, the request can be 15K+ tokens
- For 32K models, a 4096-token summary limit is often insufficient for complex sessions
- No circuit breaker: if compaction fails, the engine has no recovery path

**Consequences:**
- Session freezes, consuming CPU/RAM indefinitely (observed: 277% CPU, 11.8GB RAM for 26+ hours in Claude Code)
- User must kill the process, losing all unsaved context
- The `CheckpointManager` may not have written a checkpoint if the hang occurs mid-compaction

**Prevention:**
1. Add a timeout to `CompactService.compact()` (e.g., 60 seconds)
2. Implement a fallback: if compaction fails, truncate oldest messages instead
3. Cap the input to compaction (e.g., max 50% of context window)
4. Add a circuit breaker: after 3 consecutive compaction failures, force checkpoint + halt
5. For 32K models, increase `COMPACT_MAX_OUTPUT_TOKENS` to 8192 or make it configurable

**Detection:**
- Monitor `compact()` call duration; alert if >30 seconds
- Track compaction success/failure rate
- Watch for sessions with no new messages for >5 minutes while engine is "active"

**Phase to address:** Phase 2 (Message Dehydration + Compaction)

---

### Pitfall 3: Lossy Dehydration Destroys Critical Context

**What goes wrong:** The `maybe_dehydrate_messages()` function replaces old tool results with a head/tail summary (`_cheap_summary()`). This loses error messages, exact file paths, line numbers, and debugging chains. After dehydration, the model re-attempts failed approaches or uses wrong identifiers.

**Why it happens:**
- `_cheap_summary()` keeps only 250 chars of head + 180 chars of tail
- Error stack traces, exact API responses, and file contents are discarded
- The dehydration threshold (`len(joined) < 1200`) is arbitrary; small but critical outputs are lost
- No "do not dehydrate" flag for critical tool results

**Consequences:**
- Model re-reads files it already read (wasted tokens)
- Model re-attempts approaches that already failed
- Model generates code with wrong identifiers (column names, API params)
- Debugging context is lost; model cannot trace error chains

**Prevention:**
1. Add a `critical` flag to tool results that should never be dehydrated
2. Preserve error messages and stack traces in full (they are small but critical)
3. Use structured dehydration: summarize by type (file read → file path + size; grep → pattern + match count; error → full message)
4. Keep a "dehydration log" mapping dehydrated IDs to full content (for rehydration on demand)

**Detection:**
- After dehydration, check if model re-issues identical tool calls within 3 turns
- Log "dehydration regret" events (model asks for info that was just dehydrated)
- Monitor for increased tool call volume after dehydration triggers

**Phase to address:** Phase 2 (Message Dehydration + Compaction)

---

### Pitfall 4: Shell Injection via Unsanitized Tool Input

**What goes wrong:** `BashTool.execute()` passes the `command` parameter directly to `subprocess.run(cmd, shell=True, ...)`. Any malicious command crafted by the LLM (or injected via prompt) executes with the user's privileges. The `SandboxManager` is opt-in and not always enabled.

**Why it happens:**
- `shell=True` is the default in `BashTool`
- No input validation on the `command` parameter
- The `dangerously_disable_sandbox` parameter exists but is not restricted
- `_run_shell` in `main.py` (line ~1360) has the same vulnerability

**Consequences:**
- Arbitrary code execution: `rm -rf /`, credential theft, backdoor installation
- CVE-2025-61260 and CVE-2025-53773 show this pattern in production tools
- Even "read-only" commands can exfiltrate data via DNS/HTTP

**Prevention:**
1. Disable `shell=True` by default; parse commands into lists and use `shell=False`
2. Add a command allowlist/blocklist regex
3. Make sandbox mode mandatory for all Bash tool executions
4. Validate that `dangerously_disable_sandbox` requires explicit user confirmation
5. Add audit logging for all Bash tool executions

**Detection:**
- Log all Bash commands; flag patterns matching `curl`, `wget`, `nc`, `bash -c`, backticks, `$()`
- Monitor for commands accessing `~/.ssh`, `~/.aws`, environment variables
- Alert on commands with shell metacharacters (`;`, `|`, `&&`, `||`)

**Phase to address:** Phase 1 (Security Hardening)

---

### Pitfall 5: File Path Traversal in File Tools

**What goes wrong:** `FileReadTool`, `FileEditTool`, `FileWriteTool`, and `GlobTool` accept arbitrary `file_path` parameters without validation. The LLM can read/write any file on the system, including `/etc/passwd`, `~/.ssh/id_rsa`, or source code outside the project.

**Why it happens:**
- No path sandbox or allowlist
- `Path(file_path)` is used directly without resolving or validating
- The permission system prompts for write tools but does not validate paths
- `GlobTool` uses `rg` with arbitrary paths

**Consequences:**
- Data exfiltration (reading sensitive files)
- Supply chain attacks (modifying `requirements.txt`, `package.json`)
- Credential theft (reading `.env` files)
- Code poisoning (injecting backdoors into source files)

**Prevention:**
1. Add a `PathSandbox` that restricts all file operations to the project root
2. Validate that resolved paths are within the project root before any I/O
3. Add an allowlist for sensitive files (`.env`, `*.key`, `*.pem`) that requires explicit user approval
4. Normalize paths with `Path.resolve()` and check for traversal (`..` components)

**Detection:**
- Log all file operations outside the project root
- Alert on reads of files matching `.*secret.*`, `.*credential.*`, `*.pem`, `*.key`
- Monitor for writes to files not in version control

**Phase to address:** Phase 1 (Security Hardening)

---

### Pitfall 6: Unvalidated Regex in GrepTool (ReDoS)

**What goes wrong:** `GrepTool.execute()` passes the `pattern` parameter directly to `re.compile(pattern)` and `rg`. Malformed or malicious regex patterns can cause `re.error` or ReDoS (Regular Expression Denial of Service) on large files.

**Why it happens:**
- No regex validation before compilation
- No timeout on regex execution in the Python fallback (`_python_grep`)
- Patterns like `(a+)+$` on large inputs cause exponential backtracking
- The `rg` timeout is 30 seconds, but the Python fallback has no timeout

**Consequences:**
- Engine hangs on malicious regex (DoS)
- CPU exhaustion on the host machine
- Session becomes unresponsive

**Prevention:**
1. Wrap regex compilation in `try/except re.error`
2. Add a timeout to `_python_grep` regex execution (e.g., 5 seconds per file)
3. Reject patterns known to cause ReDoS (nested quantifiers, excessive alternation)
4. Prefer `rg` (which has its own timeout) over Python fallback

**Detection:**
- Log regex compilation failures
- Monitor GrepTool execution time; alert if >10 seconds
- Flag patterns with nested quantifiers `(a+)+`, `(a*)*`

**Phase to address:** Phase 1 (Security Hardening)

---

### Pitfall 7: Hardcoded Paths Breaking Wiki Subsystems

**What goes wrong:** Multiple wiki modules reference `.cc-mini/` as a hardcoded workspace directory. After the cleanup deleted this directory, all wiki-strict mode operations fail with `FileNotFoundError`.

**Why it happens:**
- `taskpack.py`, `post_edit_guard.py`, `reconcile.py`, `archive.py`, `maintenance.py`, `file_edit_strict.py` all hardcode `.cc-mini/`
- No centralized workspace path configuration
- The `config.py` has no setting for wiki workspace root

**Consequences:**
- Wiki-strict mode is completely non-functional
- `/prime`, `/plan`, `/scan`, `/digest` commands crash
- TaskPacks, checkpoints, and deferred issues cannot be persisted

**Prevention:**
1. Centralize workspace path in `config.py` (e.g., `WIKI_WORKSPACE_ROOT`)
2. Make all wiki modules read the path from config
3. Add workspace directory auto-creation with `mkdir(parents=True, exist_ok=True)`
4. Add a startup check that validates workspace paths exist

**Detection:**
- Run wiki-strict mode smoke tests on every build
- Monitor for `FileNotFoundError` in wiki module logs
- Validate that `.cc-mini/` exists on startup

**Phase to address:** Phase 1 (Wiki Infrastructure Fix)

---

### Pitfall 8: Missing Error Handling in /dream Command

**What goes wrong:** The `/dream` command (`_cmd_dream`) calls `ctx.run_dream()` without any try/except. If `run_dream` raises an exception, the error propagates uncaught, potentially crashing the REPL or losing messages.

**Why it happens:**
- `_cmd_dream` is a thin wrapper with no error handling
- `run_dream` is passed as a callable from `main.py`; its implementation is opaque
- No rollback mechanism if dream consolidation fails mid-operation

**Consequences:**
- REPL crash on dream failure
- Partially written memory files (corrupted state)
- User loses unsaved conversation context

**Prevention:**
1. Wrap `ctx.run_dream()` in `try/except` with user-friendly error messages
2. Make dream operations atomic (write to temp file, then rename)
3. Add a rollback mechanism for partial dream state
4. Log dream failures for debugging

**Detection:**
- Monitor `/dream` command error rate
- Check for partially written files in memory directory
- Alert on REPL crashes correlated with `/dream` usage

**Phase to address:** Phase 1 (Bug Fixes)

---

### Pitfall 9: Zero Test Coverage in Wiki Subsystems

**What goes wrong:** The entire wiki subsystem (`taskpack.py`, `reconcile.py`, `archive.py`, `maintenance.py`, `post_edit_guard.py`, `lint.py`, `target_identity.py`) has no tests. Changes to these modules risk silent regressions.

**Why it happens:**
- Wiki-strict mode was added incrementally without test infrastructure
- Complex state machines (FlowState, TaskStatus, EntityStatus) are string-based
- File I/O and timestamp logic are difficult to test without mocking

**Consequences:**
- Refactors break wiki-strict mode silently
- Flow state typos cause silent failures
- Reconciliation logic produces false positives/negatives
- Post-edit guard misses async functions (already a known bug)

**Prevention:**
1. Add unit tests for all wiki modules with mocked filesystem
2. Use `FlowState` enum everywhere; add exhaustive transition validation
3. Add integration tests for `/prime` → `/plan` → `/post_edit` workflow
4. Test edge cases: empty taskpacks, missing entities, stale files, hash collisions

**Detection:**
- Run test coverage reports; enforce minimum coverage for wiki modules
- Add CI gate that fails if wiki file changes lack test changes
- Monitor for wiki-strict mode bug reports in user feedback

**Phase to address:** Phase 3 (Test Coverage)

---

### Pitfall 10: String-Based Flow State Machine

**What goes wrong:** `FlowState` is defined as an `Enum`, but transitions are string-based and scattered across `commands.py` and `engine.py`. A typo in a state name causes silent failures.

**Why it happens:**
- `commands.py` references flow states as raw strings (e.g., `"PLAN"`, `"LOCATE"`)
- No centralized transition validator
- The enum exists but is not enforced

**Consequences:**
- Invalid state transitions go undetected
- Wiki-strict mode workflow breaks silently
- Debugging requires grep-ing for state strings across the codebase

**Prevention:**
1. Use `FlowState.PLAN` instead of `"PLAN"` everywhere
2. Add a `FlowStateMachine` class with validated transitions
3. Raise `ValueError` on invalid transitions
4. Add type hints requiring `FlowState` enum, not `str`

**Detection:**
- Static analysis: grep for raw flow state strings
- Runtime: log all state transitions; alert on invalid ones
- Tests: verify all valid transitions and reject invalid ones

**Phase to address:** Phase 1 (Type Safety)

---

### Pitfall 11: API Key Exposure via Module-Level `load_dotenv()`

**What goes wrong:** `config.py` calls `load_dotenv()` at module import time. Environment variables are loaded into the process before any code runs, making it easy to accidentally log or leak them.

**Why it happens:**
- `load_dotenv()` is at the top of `config.py`, executed on import
- Any module importing `config.py` triggers dotenv loading
- No validation that `.env` is in `.gitignore`

**Consequences:**
- API keys logged in crash reports, debug output, or CI logs
- Keys exposed if `os.environ` is serialized (e.g., for debugging)
- `.env` files accidentally committed to Git

**Prevention:**
1. Move `load_dotenv()` to an explicit call in `main()`
2. Validate that `.env` is in `.gitignore` on startup
3. Mask API keys in all logs and error messages
4. Use `pydantic.SecretStr` for API key fields in `AppConfig`

**Detection:**
- Scan logs for patterns matching API key formats (`sk-`, `claude-`)
- Pre-commit hook checking `.env` is not staged
- CI check that no `.env` files exist in the repo

**Phase to address:** Phase 1 (Security Hardening)

---

### Pitfall 12: Race Condition in Wiki Watcher

**What goes wrong:** The file watcher thread (`watcher.py`) may miss rapid successive changes or crash on directory deletion. The `MAX_RETRY = 3` with no backoff or jitter causes rapid retries that overwhelm the filesystem.

**Why it happens:**
- No file locking or debouncing in the watcher
- `ingest_all()` and concurrent edits race for file access
- Retry logic has no exponential backoff

**Consequences:**
- Wiki entities become stale or inconsistent
- File watcher thread crashes silently
- Rapid retries cause filesystem lock contention

**Prevention:**
1. Add debouncing (e.g., 500ms delay before ingest)
2. Implement exponential backoff with jitter for retries
3. Add a maximum total retry duration (e.g., 30 seconds)
4. Use file locking or atomic writes for entity files

**Detection:**
- Monitor watcher thread health (is it alive?)
- Log retry counts and durations
- Alert on rapid successive file change events

**Phase to address:** Phase 2 (Wiki Reliability)

---

### Pitfall 13: Duplicate Function Definition Shadowing

**What goes wrong:** `_get_git_section()` is defined twice in `context.py` (lines 120-155 and 156-189). The second definition shadows the first, making the first dead code.

**Why it happens:**
- Copy-paste error during development
- No linter caught the duplicate definition
- The functions have identical bodies, so behavior appears correct

**Consequences:**
- Dead code accumulates technical debt
- Risk of diverging implementations if only one copy is updated
- Confusion for maintainers

**Prevention:**
1. Remove the duplicate definition
2. Enable `flake8` or `pylint` rules for duplicate function definitions
3. Add pre-commit hooks for linting

**Detection:**
- Static analysis with `pylint` (`R0801` duplicate code)
- Code review checklist for duplicate definitions

**Phase to address:** Phase 1 (Code Cleanup)

---

### Pitfall 14: Post-Edit Guard Missing Async Function Handling

**What goes wrong:** `_extract_ast_symbols()` only checks for `ast.ClassDef` and `ast.FunctionDef`, missing `ast.AsyncFunctionDef`. Async functions are invisible to the post-edit impact analysis.

**Why it happens:**
- The AST visitor was written for Python 3.8 syntax
- `ast.AsyncFunctionDef` was not included in the node types to visit
- No tests cover async code paths

**Consequences:**
- Post-edit guard reports false negatives for async functions
- Changes to async functions are not tracked in impact analysis
- Completion state may be incorrectly marked as clean when async functions changed

**Prevention:**
1. Add `ast.AsyncFunctionDef` to the visitor
2. Add test cases with async/await syntax
3. Consider using `ast.walk()` instead of manual visitor for completeness

**Detection:**
- Test post-edit guard on files containing `async def`
- Static analysis: grep for `ast.ClassDef`/`ast.FunctionDef` without `ast.AsyncFunctionDef`

**Phase to address:** Phase 2 (Wiki Correctness)

---

### Pitfall 15: SQLite Session Store Lock Contention

**What goes wrong:** The `SessionStore` uses a single SQLite database file. Concurrent writes from multiple `cc-mini` instances cause `database is locked` errors.

**Why it happens:**
- SQLite's default locking mode is exclusive
- No WAL (Write-Ahead Logging) mode enabled
- Multiple instances running in different terminals on the same project

**Consequences:**
- Session persistence fails silently
- Messages lost between turns
- Meta file updates fail, causing stale session listings

**Prevention:**
1. Enable WAL mode for SQLite (`PRAGMA journal_mode=WAL`)
2. Add retry logic with exponential backoff for locked database
3. Consider switching to JSONL-only storage (already partially implemented)

**Detection:**
- Log SQLite errors; alert on `database is locked`
- Monitor session persistence success rate
- Test concurrent session writes

**Phase to address:** Phase 3 (Session Reliability)

---

## Moderate Pitfalls

### Pitfall 16: Synchronous File I/O in Tool Execution

**What goes wrong:** File read/edit/write tools perform blocking I/O on the main thread. For large files, this blocks the engine loop.

**Why it happens:**
- Python's default file operations are synchronous
- The engine is not async; tools run on the main thread

**Consequences:**
- UI freezes during large file operations
- Tool execution timeout may fire incorrectly

**Prevention:**
1. Use `aiofiles` or move I/O to a thread pool
2. Add progress indicators for large operations

**Phase to address:** Phase 3 (Performance)

---

### Pitfall 17: Companion Game Terminal State Leak

**What goes wrong:** The idle adventure game uses raw ANSI escape sequences and `tty.setcbreak`. If the process crashes or is interrupted, the terminal may not restore echo or canonical mode.

**Why it happens:**
- No `try/finally` around terminal mode changes
- SIGINT or unhandled exception during game loop

**Consequences:**
- Terminal becomes unusable (no echo, no line editing)
- User must run `reset` to recover

**Prevention:**
1. Use `try/finally` or context managers for terminal state
2. Register signal handlers to restore terminal on SIGINT
3. Consider using a proper TUI library (`rich`, `blessed`)

**Phase to address:** Out of scope (companion system)

---

### Pitfall 18: Demo/Mock Code in Production Commands

**What goes wrong:** `_cmd_post_edit` in `commands.py` contains hardcoded demo patch analysis with mock content. The `/post_edit` command does not perform real analysis in production.

**Why it happens:**
- The command was implemented as a prototype
- The actual `PostEditGuard` implementation exists but is not wired in

**Consequences:**
- Users get canned demo results instead of real analysis
- Post-edit guard is effectively non-functional

**Prevention:**
1. Replace the hardcoded demo with a call to the actual `PostEditGuard`
2. Remove demo files and mock content
3. Add integration test for `/post_edit` command

**Phase to address:** Phase 2 (Wiki Correctness)

---

### Pitfall 19: Unvalidated Tool Input Schemas

**What goes wrong:** Tool `input_schema` is passed to the LLM but not validated on the Python side before `execute()` is called. Malformed or missing parameters cause `TypeError` or `KeyError` at runtime.

**Why it happens:**
- No JSON Schema validation in the tool base class
- Tools assume parameters exist without checking

**Consequences:**
- Runtime exceptions in tool execution
- Poor error messages for the user
- Potential security issues if types are wrong

**Prevention:**
1. Add `jsonschema` validation in `Tool.execute()` wrapper
2. Validate required fields and types before calling tool logic
3. Return structured error messages for validation failures

**Phase to address:** Phase 1 (Input Validation)

---

### Pitfall 20: No Rate Limiting or Retry Budget for LLM Calls

**What goes wrong:** `LLMClient` has retry logic but no global rate-limit budget or circuit breaker. API outages or rate limits can cause cascading failures.

**Why it happens:**
- `_MAX_RETRIES = 3` with fixed backoff `(1, 3, 10)`
- No tracking of retry budget across calls
- No circuit breaker for persistent failures

**Consequences:**
- API rate limits hit repeatedly
- User charged for failed retries
- Session becomes unusable during API outages

**Prevention:**
1. Add a token bucket rate limiter
2. Implement circuit breaker (open after N failures in M seconds)
3. Add jitter to backoff to prevent thundering herd
4. Track retry budget per session

**Phase to address:** Phase 3 (Resilience)

---

## Phase-Specific Warnings

| Phase | Topic | Likely Pitfall | Mitigation |
|-------|-------|---------------|------------|
| Phase 1 | Token counting | Heuristic-only estimation | Integrate tiktoken + API usage calibration |
| Phase 1 | Security | Shell injection | Disable shell=True, add sandbox |
| Phase 1 | Security | Path traversal | Add PathSandbox |
| Phase 1 | Wiki infra | Hardcoded .cc-mini/ paths | Centralize in config.py |
| Phase 1 | Bug fixes | /dream exception safety | Add try/except + atomic writes |
| Phase 1 | Type safety | String-based flow states | Enforce FlowState enum |
| Phase 2 | Dehydration | Lossy compression | Preserve errors, add critical flag |
| Phase 2 | Compaction | Hangs/timeouts | Add timeout + fallback |
| Phase 2 | Wiki correctness | Missing async handling | Add ast.AsyncFunctionDef |
| Phase 2 | Wiki reliability | Race conditions | Add debouncing + backoff |
| Phase 3 | Testing | Zero wiki coverage | Add unit + integration tests |
| Phase 3 | Performance | Sync I/O blocking | Use thread pool or aiofiles |
| Phase 3 | Resilience | No rate limiting | Add token bucket + circuit breaker |

---

## Sources

- [Claude Code Context Compaction Explained](https://okhlopkov.com/claude-code-compaction-explained/) — HIGH confidence (community analysis with source code references)
- [Claude Code Hangs During Compaction](https://github.com/anthropics/claude-code/issues/19567) — HIGH confidence (official bug report)
- [Context Compaction Loses Critical Knowledge](https://github.com/anthropics/claude-code/issues/29890) — HIGH confidence (official bug report)
- [Why Claude Loses Context After Compaction](https://docs.bswen.com/blog/2026-02-09-claude-context-loss-compaction/) — MEDIUM confidence (community analysis)
- [Stop Claude Code from Lobotomizing Itself](https://ianlpaterson.com/blog/stop-claude-code-from-lobotomizing-itself-mid-task/) — MEDIUM confidence (community workaround)
- [Prompt Injection Attacks on Agentic Coding Assistants](https://arxiv.org/html/2601.17548v1) — HIGH confidence (academic research)
- [IDEsaster: 30+ Vulnerabilities in AI Coding Tools](https://tigran.tech/securing-ai-coding-agents-idesaster-vulnerabilities/) — HIGH confidence (security research)
- [Token Estimation Accuracy Problems](https://galileo.ai/blog/tiktoken-guide-production-ai) — HIGH confidence (industry analysis)
- [Checkpoints Are Not Durable Execution](https://www.diagrid.io/blog/checkpoints-are-not-durable-execution-why-langgraph-crewai-google-adk-and-others-fall-short-for-production-agent-workflows) — HIGH confidence (industry analysis)
- cc-mini codebase analysis (`src/core/engine.py`, `src/core/token_budget.py`, `src/core/compact.py`, `src/core/dehydration.py`, `src/core/commands.py`, `src/core/tools/*.py`) — HIGH confidence (primary source)
