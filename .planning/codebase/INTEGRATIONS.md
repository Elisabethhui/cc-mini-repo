# External Integrations

**Analysis Date:** 2026-04-18

## APIs & External Services

**LLM Providers:**
- **Anthropic Messages API** — Primary provider. Streaming, tool use, token caching.
  - SDK: `anthropic` Python package (`src/core/llm.py`)
  - Auth: `ANTHROPIC_API_KEY` env var (or TOML config `anthropic.api_key`)
  - Base URL override: `ANTHROPIC_BASE_URL`
  - Default model: `claude-sonnet-4-20250514`
  - Supported models: claude-opus-4-6, claude-sonnet-4-6, claude-haiku-4-5, claude-3-7-sonnet, etc. (`src/core/config.py`)

- **OpenAI Chat Completions API** — Secondary provider. Streaming, tool calls, reasoning effort.
  - SDK: `openai` Python package (`src/core/llm.py`)
  - Auth: `OPENAI_API_KEY` env var (or TOML config `openai.api_key`)
  - Base URL override: `OPENAI_BASE_URL`
  - Default model: `gpt-5.1-codex`
  - Supports reasoning effort for gpt-5/o1/o3/o4 models (`src/core/llm.py`)

**Terminal UI:**
- `prompt_toolkit` — Local terminal UI framework (not an external service)
- `rich` — Local terminal rendering library (not an external service)

## Data Storage

**Databases:**
- None. No SQL/NoSQL database used.

**File Storage:**
- Local filesystem only.
  - Session persistence: `~/.mini-claude/sessions/{sanitized_cwd}/` — JSONL + meta JSON (`src/core/session.py`)
  - Memory system: `~/.mini-claude/memory/` — append-only daily logs, MEMORY.md index, topic files (`src/core/memory.py`)
  - Wiki workspace (wiki_strict mode): `./.cc-mini/wiki/` — entity markdown files, index (`src/core/knowledge/ingester.py`)
  - Config: `~/.config/cc-mini/config.toml`, `./.cc-mini.toml` (`src/core/config.py`)
  - History: `~/.cc_mini_history` (`src/core/main.py`)

**Caching:**
- Anthropic prompt caching (API-level, not local) — tracked in cost calculations (`src/core/cost_tracker.py`)
- No local Redis/memcached equivalent

## Authentication & Identity

**Auth Provider:**
- API key-based authentication only.
- No OAuth, SSO, or user identity system.
- API keys loaded from env vars or TOML config files (see forbidden files policy — never commit these).

## Monitoring & Observability

**Error Tracking:**
- None. No Sentry, Rollbar, or similar.

**Logs:**
- Console output via `rich.console.Console` (`src/core/main.py`)
- Session messages persisted as JSONL (`src/core/session.py`)
- Cost tracking with per-model usage summaries (`src/core/cost_tracker.py`)
- Drift log for wiki_strict mode: `./.cc-mini/drift_log.json` (`src/core/knowledge/ingester.py`)

## CI/CD & Deployment

**Hosting:**
- Not applicable. This is a local CLI tool, not a deployed service.

**CI Pipeline:**
- GitHub Actions workflow: `.github/workflows/wiki-lint.yml`
  - Triggers: push, pull_request
  - Runs on: `ubuntu-latest`
  - Steps: checkout, run `python3 scripts/wiki_check.py`, `python3 scripts/raw_manifest_check.py`, `python3 scripts/untracked_raw_check.py`
  - Note: These scripts reference deleted directories (wiki, scripts). The workflow file exists but may be non-functional after cleanup.

## Environment Configuration

**Required env vars:**
- `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` — At least one required for LLM access
- `CC_MINI_PROVIDER` — Optional (defaults to `anthropic`)

**Optional env vars:**
- `CC_MINI_MODEL`, `CC_MINI_MAX_TOKENS`, `CC_MINI_EFFORT`
- `CC_MINI_BUDDY_MODEL`, `CC_MINI_MEMORY_DIR`
- `CC_MINI_MODE` (`standard` or `wiki_strict`)
- Provider-specific base URL overrides

**Secrets location:**
- Env vars or `~/.config/cc-mini/config.toml` (user-managed, not in repo)
- `.env` files (loaded by `python-dotenv`, typically gitignored)

## Webhooks & Callbacks

**Incoming:**
- None. No HTTP server or webhook endpoints.

**Outgoing:**
- None. No outgoing webhooks.

## Sandbox / Security Integration

**bubblewrap (bwrap)** — Linux-only sandbox for Bash tool execution
- External system dependency: `bwrap` binary must be installed (`src/core/sandbox/checker.py`)
- Requires Linux user namespace support (`/proc/sys/kernel/unprivileged_userns_clone`)
- Wraps commands with read-only root, writable project directory, optional network isolation (`src/core/sandbox/wrapper.py`)
- Not available on macOS or Windows

---

*Integration audit: 2026-04-18*
