# cc-mini Stack Overview

## Language & Runtime

| Item | Value |
|------|-------|
| Language | Python 3.11+ |
| Build system | Hatchling (`hatchling.build`) |
| Package name | `cc-mini` |
| Version | `0.1.0` |
| Entry point | `cc-mini = core.main:main` |
| Source layout | `src/core/` (wheel packages `src/core`) |

## Core Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `anthropic` | `>=0.40.0` | Anthropic SDK (Claude API client) |
| `openai` | `>=1.0.0` | OpenAI SDK (GPT / o-series API client) |
| `prompt_toolkit` | `>=3.0.0` | Interactive REPL, key bindings, completion menus, input handling |
| `rich` | `>=13.0.0` | Terminal rendering (Markdown, spinners, tables, styled text) |
| `python-dotenv` | `>=1.0.0` | `.env` file loading for configuration |
| `watchdog` | *(implied by watcher.py)* | File-system watching for wiki_strict mode |

## Dev Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | `>=8.0` | Test runner |
| `pytest-asyncio` | `>=0.23` | Async test support |

## Runtime Architecture

### Entry Point — `src/core/main.py`
- Parses CLI arguments (`argparse`)
- Loads configuration via `load_app_config()`
- Initializes `Engine`, `PermissionChecker`, `SandboxManager`, `WorkerManager`
- Sets up the `prompt_toolkit`-based REPL with slash-command autocompletion
- Manages the main interaction loop (user input -> engine.submit -> output)
- Supports two invocation modes:
  - **Interactive REPL** (default): bordered prompt, streaming markdown, spinner, key bindings
  - **One-shot / piped** (`--print` or positional prompt): print response and exit

### Engine — `src/core/engine.py`
- `Engine` class: the streaming API loop
- Manages conversation with the LLM via `LLMClient`
- Handles tool calls, retries (`_MAX_RETRIES = 3`, backoff `1, 3, 10`), token budget
- Normalizes content blocks between Anthropic and OpenAI SDK formats
- Supports concurrent execution of read-only tools via `ThreadPoolExecutor`
- Integrates token-budget protection, dehydration, compaction, and checkpointing

### LLM Client — `src/core/llm.py`
- `LLMClient` abstracts Anthropic and OpenAI-compatible APIs
- Streaming: `_AnthropicStream` and `_OpenAIStream` context managers
- Error classification: authentication, retryable (rate limit, connection, server), API errors
- Content normalization: unifies `tool_use`, `tool_result`, `text`, `image` blocks across providers
- OpenAI reasoning effort support (`low` / `medium` / `high`) for GPT-5 / o-series models

### Tool System — `src/core/tools/`
All tools inherit from `Tool` base class (`base.py`) and implement:
- `to_api_schema()` — JSON schema for LLM tool definitions
- `execute()` — actual tool logic
- `is_read_only()` — auto-approval flag

| Tool | File | Read-Only | Description |
|------|------|-----------|-------------|
| `Read` | `file_read.py` | Yes | Read files with line numbers, offset/limit |
| `Edit` | `file_edit.py` | No | Exact string replacement (`old_string` -> `new_string`) |
| `Edit` (strict) | `file_edit_strict.py` | No | Wiki-strict variant of Edit |
| `Write` | `file_write.py` | No | Create or overwrite files |
| `ASTRead` | `ast_read.py` | Yes | AST-based Python code reading (symbol/span/anchor/outline) |
| `Glob` | `glob_tool.py` | Yes | File pattern matching |
| `Grep` | `grep_tool.py` | Yes | Content search via `ripgrep` (rg), fallback to Python regex |
| `Bash` | `bash.py` | No | Shell command execution with optional sandbox wrapping |
| `AskUserQuestion` | `ask_user.py` | Yes | Interactive multi-choice / multi-select prompts |
| `Agent` | `agent.py` | No | Spawn background worker tasks |
| `SendMessage` | `agent.py` | No | Continue an existing worker |
| `TaskStop` | `agent.py` | No | Stop a running worker |
| `EnterPlanMode` | `plan_tools.py` | No | Enter explore-before-implement plan mode |
| `ExitPlanMode` | `plan_tools.py` | No | Exit plan mode |

### Permission System — `src/core/permissions.py`
- `PermissionChecker`: read-only tools auto-approved; write tools (Bash, Edit, Write) prompt user
- Supports `--auto-approve` flag (dangerous, bypasses all prompts)
- Sandbox auto-allow: sandboxed Bash commands need no confirmation when `auto_allow_bash` is enabled
- Plan mode restrictions: only read-only tools + plan file writes allowed

### Configuration — `src/core/config.py`
Three-tier priority: **CLI args > Environment variables > TOML files**

TOML config files (loaded in order):
1. `~/.config/cc-mini/config.toml`
2. `.cc-mini.toml` (project-local, CWD)

Environment variables:
- `CC_MINI_MODEL`, `CC_MINI_MAX_TOKENS`, `CC_MINI_MEMORY_DIR`
- `CC_MINI_PROVIDER`, `CC_MINI_EFFORT`, `CC_MINI_BUDDY_MODEL`
- `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`
- `OPENAI_API_KEY`, `OPENAI_BASE_URL`
- `CC_MINI_MODE` (`standard` or `wiki_strict`)
- `CC_MINI_COORDINATOR` (enable coordinator mode)

`AppConfig` dataclass fields: `provider`, `api_key`, `base_url`, `model`, `max_tokens`, `effort`, `buddy_model`, `memory_dir`, `dream_interval_hours`, `dream_min_sessions`, `auto_dream`, `config_paths`.

### Session Persistence — `src/core/session.py`
- `SessionStore`: JSONL-based conversation storage
- Location: `~/.mini-claude/sessions/{sanitized_cwd}/`
- Files per session: `{session_id}.jsonl` (messages), `{session_id}.meta.json` (metadata)
- Supports listing, loading, and resuming past sessions

### Context Compression — `src/core/compact.py`
- `CompactService`: summarises old messages to free token budget
- Thresholds: model-aware (e.g., 200K context window for Claude Sonnet 4)
- Splits messages into (history to summarise, recent to keep)
- Uses the same `LLMClient` to generate structured summaries

### Token Budget — `src/core/token_budget.py`
- `TokenBudgetManager`: pre-flight and post-flight token checks
- Budget thresholds (for 32K models): soft 16K, compact 20K, checkpoint 24K, hard stop 26K
- Actions: dehydrate -> compact -> checkpoint -> hard stop

### Dehydration — `src/core/dehydration.py`
- `maybe_dehydrate_messages()`: replaces large tool_result contents with truncated summaries
- Skips recent 2 messages and error blocks
- Target: keep context under 32K for local/small models

### Checkpoint — `src/core/checkpoint.py`
- `CheckpointManager`: saves runtime checkpoints when context approaches limits
- Writes to `code-reading-notes/manifest.json`, `progress.md`, `checkpoint_report.md`
- Records: skill, reason, next skill, artifacts written, token estimate, budget state

### Memory System — `src/core/memory.py`
- KAIROS cross-session memory: append-only daily logs, dream consolidation
- Directory: `~/.mini-claude/memory/`
- Daily logs: `logs/YYYY/MM/YYYY-MM-DD.md`
- `MEMORY.md` index (max 10K chars)
- Auto-dream: consolidates logs into topic files after threshold (default 24h, 5 sessions)
- Lock file prevents concurrent consolidation

### Skill System — `src/core/skills.py`
- Skills are Markdown files with YAML frontmatter defining reusable prompts
- Three sources: **bundled** (code-registered), **project** (`.cc-mini/skills/`), **user** (`~/.cc-mini/skills/`)
- Execution modes: `inline` (prompt injected into conversation) or `fork` (isolated turn)

### Sandbox — `src/core/sandbox/`
- `SandboxManager` (`manager.py`): unified sandbox interface
- `SandboxConfig` (`config.py`): TOML-persisted settings
- `wrapper.py`: generates `bwrap` (bubblewrap) command lines
- Features: read-only root, writable allow-list, network isolation (`--unshare-net`), protected config files
- Modes: `auto-allow`, `regular`, `disabled`

### Companion / Buddy — `src/core/buddy/`
- Companion pet system with hatching, stats, mood, idle animations
- Integrates with REPL toolbar via `CompanionAnimator`
- Observer pattern for reactive commentary on assistant responses

### Wiki-Strict Subsystems — `src/core/wiki/`
Activated when `CC_MINI_MODE=wiki_strict`:
- `taskpack.py` — Structured task planning with EditSpec
- `reconcile.py` — Detect and recover stale wiki entities
- `archive.py` — Automatic archiving with age thresholds
- `query_archive.py` — Query archived items
- `lint.py` — Health checks for wiki structure
- `maintenance.py` — Lifecycle management
- `post_edit_guard.py` — Post-edit verification
- `target_identity.py` — Target disambiguation for `/prime`

### Knowledge System — `src/core/knowledge/`
- `ingester.py` — Ingests raw documents into wiki format (Python AST, Markdown headers)
- `watcher.py` — File-system watcher with debounce for incremental wiki updates
- `dehydrator.py` — Message dehydration for context compression

### Other Key Modules
- `context.py` — System prompt builder (static + dynamic sections: env, git, CLAUDE.md, memory)
- `commands.py` — Slash command parsing and dispatch (`/help`, `/compact`, `/resume`, `/plan`, `/cost`, `/model`, etc.)
- `coordinator.py` / `worker_manager.py` — Background worker system (threading-based)
- `plan.py` — Plan mode manager (explore-before-implement workflow)
- `cost_tracker.py` — Token usage and cost tracking with per-model pricing tiers
- `flow_state.py` — Flow state machine (PLAN / LOCATE / IMPLEMENT / VERIFY) for wiki_strict mode
- `_keylistener.py` — ESC key listener for turn cancellation

## Testing

- Framework: **pytest**
- Config in `pyproject.toml`:
  - `testpaths = ["tests"]`
  - `pythonpath = ["src"]`
- Dev dependencies: `pytest>=8.0`, `pytest-asyncio>=0.23`

## Key File Paths

| File | Purpose |
|------|---------|
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/pyproject.toml` | Project metadata, dependencies, build config |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/main.py` | CLI entry point, REPL loop |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/engine.py` | Streaming API loop, tool execution |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/llm.py` | LLM client abstraction (Anthropic + OpenAI) |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/config.py` | Configuration loading (CLI / env / TOML) |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/tools/base.py` | Tool base class |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/permissions.py` | Permission checker |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/session.py` | Session persistence (JSONL) |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/compact.py` | Context compression |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/context.py` | System prompt builder |
