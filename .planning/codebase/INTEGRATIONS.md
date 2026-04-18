# cc-mini External Integrations

## LLM API Providers

### Anthropic (Primary)
- **SDK**: `anthropic>=0.40.0` (`anthropic.Anthropic` client)
- **Supported models** (from `src/core/config.py` and `src/core/llm.py`):
  - `claude-sonnet-4-20250514` (default)
  - `claude-opus-4-6`, `claude-opus-4-5`, `claude-opus-4-1`, `claude-opus-4`
  - `claude-sonnet-4-6`, `claude-sonnet-4-5`, `claude-sonnet-4`
  - `claude-haiku-4-5-20251001`, `claude-3-7-sonnet`, `claude-3-5-sonnet`, `claude-3-5-haiku`, `claude-3-haiku`
- **Model aliases**: `sonnet`, `opus`, `haiku`, `best`
- **Max output tokens**: 4K–64K depending on model (default fallback: 32K)
- **Auth**: `ANTHROPIC_API_KEY` env var or TOML config `[anthropic] api_key`
- **Custom base URL**: `ANTHROPIC_BASE_URL` env var or TOML config `[anthropic] base_url`
- **Streaming**: Native `messages.stream()` via `_AnthropicStream`
- **Error types handled**: `AuthenticationError`, `RateLimitError`, `APIConnectionError`, `InternalServerError`, `APIError`
- **Prompt caching**: Usage tracking for `cache_read_input_tokens` and `cache_creation_input_tokens`

### OpenAI (Secondary)
- **SDK**: `openai>=1.0.0` (`openai.OpenAI` client)
- **Supported models**:
  - `gpt-5.1-codex` (default for OpenAI provider)
  - `gpt-5`, `gpt-4.1`, `gpt-4o`
  - `o1`, `o3`, `o4` (reasoning models with `reasoning_effort` support)
- **Max output tokens**: 8K–32K depending on model (default fallback: 8K)
- **Auth**: `OPENAI_API_KEY` env var or TOML config `[openai] api_key`
- **Custom base URL**: `OPENAI_BASE_URL` env var or TOML config `[openai] base_url` (supports OpenAI-compatible proxies)
- **Streaming**: SSE chunks via `_OpenAIStream` with tool call accumulation
- **Error types handled**: `AuthenticationError`, `RateLimitError`, `APIConnectionError`, `InternalServerError`, `APIError`
- **Reasoning effort**: `low` / `medium` / `high` for supported models

### Local / MLX Models (Experimental)
- `src/core/config.py` has special handling for provider `"local"` or model names containing `"mlx"`
- Forces `max_tokens = 32000` for local 32K context constraints

## Databases / Persistence

### Session Storage (JSONL)
- **Type**: File-based (JSON Lines)
- **Location**: `~/.mini-claude/sessions/{sanitized_cwd}/`
- **Files**: `{session_id}.jsonl` (messages), `{session_id}.meta.json` (metadata)
- **Implementation**: `src/core/session.py` — `SessionStore` class
- **Features**: append-only writes, auto-generated titles, session listing/resuming

### Memory / KAIROS System
- **Type**: File-based Markdown logs + index
- **Location**: `~/.mini-claude/memory/` (configurable via `--memory-dir` or `CC_MINI_MEMORY_DIR`)
- **Daily logs**: `logs/YYYY/MM/YYYY-MM-DD.md`
- **Index**: `MEMORY.md` (max 10,000 chars)
- **Consolidation lock**: `.consolidate-lock` (PID-based, 1-hour stale timeout)
- **Implementation**: `src/core/memory.py`

### Wiki Entities (wiki_strict mode)
- **Type**: Markdown files with YAML frontmatter
- **Location**: `{cwd}/.cc-mini/wiki/entities/`
- **Index**: `{cwd}/.cc-mini/wiki/index.md`
- **Drift log**: `{cwd}/.cc-mini/drift_log.json`
- **Deferred issues**: `{cwd}/.cc-mini/deferred_issues.md`
- **Implementation**: `src/core/knowledge/ingester.py`, `src/core/knowledge/watcher.py`

### Checkpoint / Progress Tracking
- **Type**: JSON + Markdown
- **Location**: `{cwd}/code-reading-notes/`
- **Files**: `manifest.json`, `progress.md`, `checkpoint_report.md`
- **Implementation**: `src/core/checkpoint.py`

### TaskPacks (wiki_strict mode)
- **Type**: JSON files
- **Location**: `{cwd}/.cc-mini/taskpacks/`
- **Implementation**: `src/core/wiki/taskpack.py`

## Auth Providers

No external OAuth or SSO integrations. Authentication is API-key based:

| Provider | Key Source | Env Var | TOML Section |
|----------|-----------|---------|--------------|
| Anthropic | API key | `ANTHROPIC_API_KEY` | `[anthropic] api_key` |
| OpenAI | API key | `OPENAI_API_KEY` | `[openai] api_key` |

## Sandbox / Security

### Bubblewrap (bwrap)
- **External dependency**: `bwrap` binary (Linux only)
- **Purpose**: Isolate Bash tool execution
- **Features**:
  - Read-only root filesystem (`--ro-bind / /`)
  - Writable directory allow-list (`--bind`)
  - Network namespace isolation (`--unshare-net`)
  - PID namespace isolation (`--unshare-pid`)
  - Protected config files (`.cc-mini.toml`, `~/.config/cc-mini/config.toml`, `CLAUDE.md`)
- **Modes**: `auto-allow` (auto-approve sandboxed bash), `regular` (still confirm), `disabled`
- **Implementation**: `src/core/sandbox/wrapper.py`, `src/core/sandbox/manager.py`

## File System Tools

### ripgrep (rg)
- **External dependency**: `rg` binary
- **Purpose**: `GrepTool` backend for fast regex search
- **Fallback**: Pure Python regex search if `rg` not installed
- **Implementation**: `src/core/tools/grep_tool.py`

### Git
- **External dependency**: `git` binary
- **Usage**: Branch detection, status, recent commits (injected into system prompt)
- **Implementation**: `src/core/context.py` (`_get_git_section`)

## Webhooks / External Services

None. cc-mini is a fully local CLI application with no webhook listeners, no HTTP server, and no callbacks.

## Environment Variables Summary

| Variable | Purpose |
|----------|---------|
| `CC_MINI_MODEL` | Default model name |
| `CC_MINI_MAX_TOKENS` | Default max output tokens |
| `CC_MINI_PROVIDER` | API provider (`anthropic` or `openai`) |
| `CC_MINI_EFFORT` | Reasoning effort (`low`/`medium`/`high`) |
| `CC_MINI_BUDDY_MODEL` | Model for companion side-features |
| `CC_MINI_MEMORY_DIR` | Override memory directory path |
| `CC_MINI_MODE` | Run mode (`standard` or `wiki_strict`) |
| `CC_MINI_COORDINATOR` | Enable coordinator mode (`1`/`true`/`yes`) |
| `ANTHROPIC_API_KEY` | Anthropic API authentication |
| `ANTHROPIC_BASE_URL` | Custom Anthropic API base URL |
| `OPENAI_API_KEY` | OpenAI API authentication |
| `OPENAI_BASE_URL` | Custom OpenAI-compatible base URL |

## Configuration Files

| File | Format | Purpose |
|------|--------|---------|
| `~/.config/cc-mini/config.toml` | TOML | Global user configuration |
| `.cc-mini.toml` (CWD) | TOML | Project-local configuration |
| `~/.cc_mini_history` | Plain text | REPL command history (prompt_toolkit FileHistory) |
| `CLAUDE.md` (CWD) | Markdown | Project instructions injected into system prompt |

## Key Integration File Paths

| File | Purpose |
|------|---------|
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/llm.py` | LLM provider abstraction (Anthropic + OpenAI) |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/config.py` | Configuration loading (env vars, TOML, CLI args) |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/session.py` | Session persistence (JSONL) |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/memory.py` | KAIROS memory system |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/sandbox/manager.py` | Sandbox manager (bwrap integration) |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/sandbox/wrapper.py` | bwrap command generation |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/tools/grep_tool.py` | ripgrep integration |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/knowledge/ingester.py` | Wiki entity ingestion |
| `/Users/huguoqing/zzzhu/code/exp/RAG/project1/cc-mini-repo/.worktrees/project-cleanup/src/core/checkpoint.py` | Checkpoint/progress persistence |
