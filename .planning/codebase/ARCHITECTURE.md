# Architecture

**Analysis Date:** 2026-04-18

## Pattern Overview

**Overall:** Interactive REPL with an agentic tool-loop, modeled after Claude Code's architecture. Supports two runtime modes: `standard` (default) and `wiki_strict` (structured workflow with AST-based code reading, strict patch verification, and automated lifecycle management for 32K token contexts).

**Key Characteristics:**
- Streaming API loop with tool-use / tool-result cycles
- Read-only tools auto-approved; write tools require user confirmation
- Dual-mode operation: standard vs. wiki_strict with state-machine enforcement
- Token budget management with dehydration, compaction, and checkpointing
- Background worker system for coordinator mode
- Session persistence via JSONL + metadata files
- Skill system for reusable prompt-based commands

## Layers

**CLI / REPL Layer:**
- Purpose: User-facing terminal interface, argument parsing, input/output rendering
- Location: `src/core/main.py`
- Contains: `main()`, `run_query()`, `_bordered_prompt()`, `_StreamingMarkdown`, `_SpinnerManager`
- Depends on: Engine, PermissionChecker, SessionStore, CompactService, commands, skills, buddy, sandbox
- Used by: End user (direct invocation via `cc-mini` entry point)

**Engine Layer:**
- Purpose: Core streaming API loop; manages LLM conversation, tool calls, retries, token budgets
- Location: `src/core/engine.py`
- Contains: `Engine` class, `AbortedError`
- Depends on: LLMClient, Tool, PermissionChecker, TokenBudgetManager, CheckpointManager, CompactService
- Used by: `main.py` (REPL), `worker_manager.py` (background workers)

**LLM Abstraction Layer:**
- Purpose: Normalize Anthropic and OpenAI SDKs behind a single interface
- Location: `src/core/llm.py`
- Contains: `LLMClient`, `_AnthropicStream`, `_OpenAIStream`, content normalization helpers
- Depends on: `anthropic`, `openai`, `httpx`
- Used by: `engine.py`, `compact.py`

**Tool System Layer:**
- Purpose: All file, shell, search, and agent tools
- Location: `src/core/tools/`
- Contains: `base.py` (abstract `Tool` class), file read/edit/write, Bash, Glob, Grep, AskUser, Agent, ASTRead, plan_tools, error_handler, reanchor
- Depends on: sandbox (for Bash wrapping)
- Used by: `engine.py` (registered at startup)

**Configuration Layer:**
- Purpose: Load settings from CLI args, env vars, and TOML files
- Location: `src/core/config.py`
- Contains: `AppConfig`, `load_app_config()`, `RunMode` enum
- Depends on: `python-dotenv`, `tomllib`
- Used by: `main.py` (bootstrapping)

**Context / Prompt Layer:**
- Purpose: Build the system prompt from static and dynamic sections
- Location: `src/core/context.py`
- Contains: `build_system_prompt()`, section builders (intro, system, tasks, actions, tools, tone, git, env)
- Depends on: `memory.py`, `buddy.prompt`
- Used by: `main.py` (engine initialization)

**Session Persistence Layer:**
- Purpose: Save/restore conversation history
- Location: `src/core/session.py`
- Contains: `SessionStore`, `SessionMeta`
- Depends on: standard library only
- Used by: `main.py`, `commands.py`

**Sandbox Layer:**
- Purpose: Bubblewrap-based command isolation
- Location: `src/core/sandbox/`
- Contains: `manager.py`, `config.py`, `checker.py`, `wrapper.py`, `command_matcher.py`
- Depends on: `bwrap` system binary
- Used by: `main.py`, `tools/bash.py`

**Wiki-Strict Subsystem:**
- Purpose: Structured workflow for 32K token contexts
- Location: `src/core/wiki/`
- Contains: `taskpack.py`, `reconcile.py`, `archive.py`, `query_archive.py`, `lint.py`, `maintenance.py`, `post_edit_guard.py`, `target_identity.py`
- Depends on: knowledge ingester
- Used by: `commands.py` (slash commands `/prime`, `/plan`, `/scan`, `/digest`, `/post_edit`)

**Knowledge System Layer:**
- Purpose: Ingest raw documents into wiki format, watch for changes, dehydrate messages
- Location: `src/core/knowledge/`
- Contains: `ingester.py`, `watcher.py`, `dehydrator.py`
- Depends on: AST parsing (`ast` module)
- Used by: `main.py` (wiki_strict startup), `commands.py`

**Companion (Buddy) Layer:**
- Purpose: Optional companion pet with mood, idle animation, and a roguelike minigame
- Location: `src/core/buddy/`
- Contains: `companion.py`, `animator.py`, `mood.py`, `observer.py`, `storage.py`, `render.py`, `sprites.py`, `poke_game/`
- Depends on: rich console
- Used by: `main.py` (toolbar integration), `commands.py` (`/buddy` command)

## Data Flow

**Standard Query Flow:**

1. User input enters `main.py` via `_bordered_prompt()`
2. `run_query()` initializes `EscListener` and `_SpinnerManager`
3. `engine.submit()` appends user message and enters the API loop
4. `LLMClient.stream_messages()` streams text chunks back
5. On `tool_use` blocks, `engine` batches read-only tools for parallel execution via `ThreadPoolExecutor`
6. Write tools (Edit, Write, Bash) execute sequentially with permission checks
7. Tool results are appended as user messages; loop continues until no more tool calls
8. `engine` persists each message to `SessionStore`

**Token Budget Protection Flow:**

1. Pre-flight: `TokenBudgetManager.estimate_from_messages()` estimates tokens
2. If over soft limit: `maybe_dehydrate_messages()` replaces old tool results with summaries
3. If over compact limit: `CompactService.compact()` summarizes old messages
4. If over checkpoint limit: `CheckpointManager.write_checkpoint()` saves state and halts
5. Post-flight: usage from API response triggers another budget check

**Wiki-Strict Flow:**

1. `main.py` detects `RunMode.WIKI_STRICT` on startup
2. `WikiIngester.ingest_all()` scans workspace and builds AST-based wiki entities
3. `start_wiki_watcher()` mounts a filesystem watcher thread
4. Commands like `/prime` use `TargetResolver` and `TaskPackManager` to generate structured task packs
5. `/plan` generates `EditSpec` objects with deferred-issue tracking
6. Post-edit `/post_edit` runs `PostEditGuard` to analyze impact and verify completion

**Coordinator Mode Flow:**

1. `--coordinator` flag or env var enables coordinator mode
2. `WorkerManager` spawns background `Engine` instances in daemon threads
3. Workers execute prompts autonomously and enqueue XML notifications
4. `main.py` drains notifications between REPL turns

## Key Abstractions

**Tool:**
- Purpose: Uniform interface for all LLM-callable operations
- Examples: `src/core/tools/base.py`, `src/core/tools/file_read.py`, `src/core/tools/bash.py`
- Pattern: Abstract base class with `name`, `description`, `input_schema`, `execute()`, `is_read_only()`

**Engine:**
- Purpose: Encapsulates the full conversation state and API loop
- Examples: `src/core/engine.py`
- Pattern: Stateful class holding messages, tools, system prompt, and budget/checkpoint managers

**LLMClient:**
- Purpose: Provider-agnostic API client
- Examples: `src/core/llm.py`
- Pattern: Normalizes Anthropic and OpenAI streaming into a common iterator interface

**CommandContext:**
- Purpose: Bundle of dependencies passed to every slash command handler
- Examples: `src/core/commands.py`
- Pattern: `@dataclass` containing engine, session store, compact service, console, config, etc.

## Entry Points

**CLI Entry Point:**
- Location: `src/core/main.py:main()`
- Triggers: `cc-mini` console script (defined in `pyproject.toml`)
- Responsibilities: Parse args, load config, initialize sandbox/memory/skills, build engine, start REPL

**One-Shot Mode:**
- Location: `src/core/main.py:main()` (when `--print` or `args.prompt` is provided)
- Triggers: `cc-mini "prompt"` or piped input
- Responsibilities: Run single turn, print response, exit

**Wiki-Strict Startup:**
- Location: `src/core/main.py:main()` (block near line 1044)
- Triggers: `CC_MINI_MODE=wiki_strict` or `--mode wiki_strict`
- Responsibilities: Ingest workspace, start file watcher, inject wiki-strict tools (ASTRead, FileEditStrict)

## Error Handling

**Strategy:** Layered: retryable API errors are retried with exponential backoff; non-retryable API errors pop the user message and yield an error event; tool execution errors return `ToolResult(is_error=True)`; aborts raise `AbortedError` which cancels the turn.

**Patterns:**
- API retries: `_MAX_RETRIES = 3` with `_RETRY_BACKOFF = (1, 3, 10)` in `engine.py`
- Tool errors: wrapped in `ToolResult` with `is_error=True`, displayed in red by the REPL
- Budget overflow: checkpoint saved and loop terminated gracefully
- Sandbox dependency errors: checked at startup; sandbox falls back to disabled if deps missing

## Cross-Cutting Concerns

**Logging:** Console output via `rich.console.Console`. No structured logging framework.

**Validation:** Input validation in `config.py` (model names, token counts, effort levels). Tool input schemas validated by the LLM API.

**Authentication:** API keys loaded from env vars (`ANTHROPIC_API_KEY`, `OPENAI_API_KEY`) or TOML config. No custom auth system.

---

*Architecture analysis: 2026-04-18*
