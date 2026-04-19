# Phase 1: Foundation & Security - Context

**Gathered:** 2026-04-20
**Status:** Ready for planning
**Mode:** Auto (decisions selected from research recommendations)

<domain>
## Phase Boundary

Close security vulnerabilities, fix token counting accuracy, and repair wiki-strict mode infrastructure so that the codebase is safe and functional before adding new context management features.

**In scope:** Security hardening (BashTool, file tools, GrepTool, config), accurate token counting, wiki workspace path fixes, /dream and /plan bug fixes, FlowState enum enforcement.
**Out of scope:** Context compression algorithms, sliding window implementation, new test suites (those belong in Phases 2-3).
</domain>

<decisions>
## Implementation Decisions

### Token Counting Strategy
- **D-01:** Use dual-path token counting: `tiktoken` (>=0.12.0) for OpenAI models, `anthropic.beta.messages.count_tokens()` for Claude models. This is the only way to achieve <5% error for both providers.
- **D-02:** Remove the 1.5x safety multiplier in `engine.py` pre-flight checks. The multiplier was a band-aid for inaccurate heuristic counting; with accurate tokenizers it causes premature checkpointing.
- **D-03:** Maintain a running calibration factor comparing API-reported usage against local estimates to detect tokenizer drift.

### Security Hardening Priority
- **D-04:** Fix BashTool `shell=True` vulnerability first (CVE-class severity). Parse commands into argument lists with `shlex.split()`, use `shell=False` by default, and make bubblewrap sandbox mandatory for all Bash execution.
- **D-05:** Add `PathSandbox` to all file tools (read/edit/write/glob) restricting operations to project root. Normalize paths with `Path.resolve()` before validation.
- **D-06:** Add regex validation and 5-second timeout to GrepTool to prevent ReDoS attacks on malformed patterns.
- **D-07:** Move `load_dotenv()` from module import time to explicit call in `main()`. Add `.env` to `.gitignore` validation.

### Wiki Infrastructure
- **D-08:** Replace all hardcoded `.cc-mini/` paths with configurable workspace directory from `config.py`. Default to `.cc-mini/` if not specified for backward compatibility.
- **D-09:** Fix `/dream` command with `try/finally` to ensure `engine.messages` is restored even if `run_query()` raises an exception.
- **D-10:** Fix `/plan` type safety by importing `PlanModeManager` in `commands.py` and typing `plan_manager` correctly instead of `object`.
- **D-11:** Enforce `FlowState` enum for all state transitions. Replace string-based state names in `commands.py` and `engine.py` with enum members. Add exhaustive transition validation.
- **D-12:** Fix `PostEditGuard` to handle `ast.AsyncFunctionDef` in `_extract_ast_symbols()`.
- **D-13:** Add debouncing (500ms) and exponential backoff to wiki watcher to prevent race conditions on rapid file changes.

### Budget State Machine
- **D-14:** Implement explicit budget states: `NORMAL -> WARNING -> COMPACT -> CHECKPOINT -> HARD_STOP`.
- **D-15:** Model-aware thresholds: 32K models use soft=16K / compact=20K / checkpoint=24K / hard_stop=26K. 200K models use soft=100K / compact=120K / checkpoint=150K / hard_stop=180K.

### Claude's Discretion
- Error message formatting for security violations — use existing `ToolResult(is_error=True)` pattern with red console output.
- Whether to log security violations to an audit file — not in this phase; defer to v2.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Security
- `.planning/research/PITFALLS.md` §"Shell Injection via Unsanitized Tool Input" — CVE details and prevention strategies
- `.planning/research/PITFALLS.md` §"File Path Traversal in File Tools" — Path sandbox requirements
- `src/core/tools/bash.py` — Current BashTool implementation (line ~70)
- `src/core/tools/file_read.py` — Current FileReadTool
- `src/core/tools/file_edit.py` — Current FileEditTool
- `src/core/tools/file_write.py` — Current FileWriteTool
- `src/core/tools/glob_tool.py` — Current GlobTool
- `src/core/tools/grep_tool.py` — Current GrepTool

### Token Counting
- `.planning/research/STACK.md` §"Token counting" — Library versions and rationale
- `src/core/token_budget.py` — Current heuristic implementation
- `src/core/engine.py` — Pre-flight budget checks (line ~263 for 1.5x multiplier)

### Wiki Infrastructure
- `.planning/research/PITFALLS.md` §"Hardcoded `.cc-mini/` paths" — Impact and fix approach
- `src/core/commands.py` — `/dream` and `/plan` command handlers
- `src/core/main.py` — `_run_dream()` implementation (line ~658)
- `src/core/wiki/taskpack.py` — TaskPack/EditSpec definitions
- `src/core/wiki/post_edit_guard.py` — AST symbol extraction
- `src/core/flow_state.py` — FlowState enum definition
- `src/core/knowledge/watcher.py` — File watcher implementation

### Configuration
- `src/core/config.py` — AppConfig and RunMode definitions
- `.planning/PROJECT.md` §Requirements — Active requirements mapped to this phase
- `.planning/REQUIREMENTS.md` — Full requirement IDs: SEC-01..05, TOK-01..04, WIK-01..06
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TokenBudgetManager` class in `token_budget.py` — Threshold definitions exist, only counting method needs replacement.
- `PermissionChecker` in `permissions.py` — Already handles y/n/always prompts; reuse for sandbox enforcement.
- `SandboxManager` in `sandbox/` — Bubblewrap wrapper exists; change from opt-in to mandatory.
- `FlowState` enum in `flow_state.py` — Already defined; just needs to be used everywhere.
- `CheckpointManager` in `checkpoint.py` — Save/restore logic exists; fix paths and add resume.

### Established Patterns
- Tool execution returns `ToolResult(is_error=True)` for failures — security violations should follow this pattern.
- Engine pre-flight checks token budget before each API call — token counting integration point.
- `config.py` uses dataclass with `load_app_config()` — workspace path should be added here.
- Commands use `CommandContext` dataclass — `plan_manager` type fix fits existing pattern.

### Integration Points
- `engine.py:submit()` — Pre-flight budget check (integrate accurate counting here).
- `engine.py` post-flight — After API response, compare estimated vs actual tokens.
- `main.py:main()` — Wiki-strict startup block (line ~1044) where workspace path is used.
- `tools/bash.py:execute()` — Where `shell=True` is used; primary security fix location.
- `commands.py` slash command registry — Where `/dream` and `/plan` are registered.
</code_context>

<specifics>
## Specific Ideas

- The `1.5x` multiplier in `engine.py` is at approximately line 263 based on codebase audit. Remove it entirely.
- `/dream` message restoration bug is at `main.py:658` — `engine.messages = saved_messages` is not in a `finally` block.
- `commands.py:244` already has a hint message about `/dream` — keep this UX but make it actually work.
- Hardcoded `.cc-mini/` paths are in: `taskpack.py`, `post_edit_guard.py`, `reconcile.py`, `archive.py`, `maintenance.py`, `file_edit_strict.py`.
</specifics>

<deferred>
## Deferred Ideas

- Audit logging for tool executions (security forensics) — belongs in v2 resilience work
- Automatic security scan on startup — new capability, defer to security-focused phase
- Tool result artifact storage — belongs in Phase 4 differentiators
- Observation masking (zero-cost compression) — belongs in Phase 4
- Dynamic tool loadout — belongs in Phase 4

None — discussion stayed within phase scope
</deferred>

---

*Phase: 01-foundation-security*
*Context gathered: 2026-04-20*
