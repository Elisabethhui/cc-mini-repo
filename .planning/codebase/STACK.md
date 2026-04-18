# Technology Stack

**Analysis Date:** 2026-04-18

## Languages

**Primary:**
- Python 3.11+ — Entire codebase (src/, tests/, scripts)

**Secondary:**
- TOML — Configuration files (`pyproject.toml`, `.cc-mini.toml`, `config.toml`)
- Markdown — Documentation, wiki entities, skill definitions, memory logs
- YAML — GitHub Actions workflow (`.github/workflows/wiki-lint.yml`)
- Shell — Install script (`install.sh`), validation scripts

## Runtime

**Environment:**
- CPython 3.11 or higher (`requires-python = ">=3.11"` in `pyproject.toml`)

**Package Manager:**
- pip (standard Python packaging)
- Build backend: `hatchling` (`pyproject.toml` line 2-3)
- Lockfile: Not present (no `requirements.txt` or `uv.lock` detected)

## Frameworks

**Core:**
- `prompt_toolkit` >=3.0.0 — REPL input handling, key bindings, autocompletion, history (`src/core/main.py`)
- `rich` >=13.0.0 — Terminal rendering, markdown streaming, spinners, tables (`src/core/main.py`, `src/core/commands.py`)
- `anthropic` >=0.40.0 — Anthropic API client (Messages API, streaming) (`src/core/llm.py`)
- `openai` >=1.0.0 — OpenAI API client (Chat Completions, streaming, tool calls) (`src/core/llm.py`)

**Testing:**
- `pytest` >=8.0 — Test runner (`pyproject.toml` line 18, `tests/`)
- `pytest-asyncio` >=0.23 — Async test support (`pyproject.toml` line 18)

**Build/Dev:**
- `hatchling` — PEP 517 build backend (`pyproject.toml` line 3)
- `python-dotenv` >=1.0.0 — `.env` file loading (`src/core/config.py` line 18)

## Key Dependencies

**Critical:**
- `anthropic` — Primary LLM provider SDK. Supports Messages API, streaming, token caching (`src/core/llm.py`)
- `openai` — Secondary LLM provider SDK. Supports Chat Completions, reasoning effort, tool calls (`src/core/llm.py`)
- `prompt_toolkit` — Interactive REPL framework with custom bordered input, slash-command autocompletion, key bindings (`src/core/main.py`)
- `rich` — Rich text and markdown rendering in terminal, live spinners, console output (`src/core/main.py`)

**Infrastructure:**
- `httpx` — HTTP client (transitive dependency via anthropic/openai; used directly for retryable error detection in `src/core/llm.py`)
- `python-dotenv` — Loads `.env` files for configuration (`src/core/config.py`)

**Standard Library (heavily used):**
- `argparse` — CLI argument parsing (`src/core/main.py`)
- `ast` — Python AST parsing for wiki-strict mode code analysis (`src/core/knowledge/ingester.py`)
- `json`, `jsonl` — Session persistence, tool result serialization (`src/core/session.py`, `src/core/memory.py`)
- `pathlib` — File system operations throughout
- `subprocess` — Bash tool execution, sandbox wrapper (`src/core/tools/bash.py`, `src/core/sandbox/wrapper.py`)
- `threading` — Background companion observer, wiki watcher, worker manager (`src/core/main.py`, `src/core/knowledge/watcher.py`)
- `tomllib` (Python 3.11+) — TOML config parsing (`src/core/config.py`)

## Configuration

**Environment:**
- `.env` file support via `python-dotenv` (loaded in `src/core/config.py`)
- Key env vars (defined in `src/core/config.py`):
  - `CC_MINI_PROVIDER` — LLM provider (`anthropic` or `openai`)
  - `CC_MINI_MODEL` — Model name
  - `CC_MINI_MAX_TOKENS` — Output token limit
  - `CC_MINI_EFFORT` — Reasoning effort (`low`/`medium`/`high`)
  - `CC_MINI_BUDDY_MODEL` — Companion model override
  - `CC_MINI_MEMORY_DIR` — Memory directory path
  - `CC_MINI_MODE` — Run mode (`standard` or `wiki_strict`)
  - `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`
  - `OPENAI_API_KEY`, `OPENAI_BASE_URL`

**Build:**
- `pyproject.toml` — Project metadata, dependencies, build config, pytest config
- `src/core/config.py` — Runtime configuration loader with TOML file support
  - Default config paths: `~/.config/cc-mini/config.toml`, `./.cc-mini.toml`

**Test:**
- `pyproject.toml` lines 26-28: `testpaths = ["tests"]`, `pythonpath = ["src"]`

## Platform Requirements

**Development:**
- Python 3.11+
- Linux (for full sandbox functionality via bubblewrap)
- macOS (sandbox disabled, REPL and tools work)

**Production:**
- Local CLI tool / REPL — no server deployment
- Data persisted to `~/.mini-claude/` (sessions, memory, logs)
- Wiki workspace written to `./.cc-mini/` (when in wiki_strict mode)

---

*Stack analysis: 2026-04-18*
