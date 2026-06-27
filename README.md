<div align="center">

# cc-mini

**AI Coding Harness with Wiki-Strict Mode**

**Agentic** · **Wiki-Strict Mode** · **Built to Extend** · **From Claude Code**

</div>

---

## Overview

cc-mini is an AI coding assistant harness implementing core Claude Code features: interactive REPL, agentic tool loop, permission system, and session persistence. It supports two runtime modes:

- **standard** — Default interactive REPL with full tool access
- **wiki_strict** — Structured workflow mode with AST-based code reading and a constrained wiki lifecycle

The later runtime-isolation phases keep `standard` stable while making `wiki_strict` visibly more constrained and mode-specific. Phase 4 focuses on clearer runtime separation, not a full double-runtime rewrite.

The current codebase is evolving toward a **Phase 1 minimal product startup** shape:

- can run
- can initialize a workspace
- can scan and prime a task
- can produce structured analysis output
- defers patch, post-edit, and maintenance hardening to later phases

---

## Quick Start

### Requirements

- Python 3.11+
- An API key for [Anthropic](https://console.anthropic.com/) or any OpenAI-compatible provider

### Install

```bash
git clone https://github.com/e10nMa2k/cc-mini.git
cd cc-mini
pip install -e ".[dev]"
```

Or use the one-line installer:

```bash
curl -fsSL https://raw.githubusercontent.com/e10nMa2k/cc-mini/main/install.sh | bash
```

### Set API Key

```bash
# Anthropic
export ANTHROPIC_API_KEY=sk-ant-...

# Or OpenAI-compatible
export CC_MINI_PROVIDER=openai
export OPENAI_API_KEY=sk-...
export OPENAI_BASE_URL=https://your-gateway.example.com/v1
```

### Run

```bash
cc-mini                              # Interactive REPL
cc-mini "what tests exist?"          # One-shot prompt
cc-mini -p "summarize this codebase" # Print and exit
cc-mini --auto-approve               # Skip permission prompts
cc-mini --resume 1                   # Resume previous session
cc-mini --coordinator                # Coordinator mode
cc-mini --mode wiki_strict           # Wiki-strict mode
```

### Phase 1 Target Workflow

The first product slice is intentionally smaller than the full lifecycle:

1. start the CLI
2. initialize the workspace
3. verify the environment
4. enter `standard` or `wiki_strict`
5. run the minimal analysis chain

The design target is to make the first successful path obvious and short:

- workspace bootstrap
- scan
- task priming
- structured planning output

Patch, post-edit, and maintenance belong to later phases and are not part of the Phase 1 minimal startup path.

### Workflow Helpers

A set of read-only slash commands helps keep tasks bounded and recoverable:

| Command | Description |
|---------|-------------|
| `/workflow-status` | Read-only workflow readiness status |
| `/workflow-init` | Create missing workflow scaffold files `[--dry-run]` |
| `/workflow-doctor` | Read-only workflow diagnostics |
| `/workflow-test` | Read-only test recommendations from changed files |

These commands do not modify source files, run tests automatically, or commit changes.  See `docs/workflow.md` for details.

---

## Configuration

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API key |
| `ANTHROPIC_BASE_URL` | Custom Anthropic gateway (optional) |
| `OPENAI_API_KEY` | OpenAI-compatible API key |
| `OPENAI_BASE_URL` | Custom OpenAI gateway URL (also used for local MLX/OMLX servers) |
| `CC_MINI_PROVIDER` | `anthropic` or `openai` |
| `CC_MINI_MODEL` | Model name (e.g. `claude-sonnet-4-6`) |
| `CC_MINI_MAX_TOKENS` | **Max output tokens** per response (not the full context window) |
| `CC_MINI_MAX_OUTPUT_TOKENS` | Alias for `CC_MINI_MAX_TOKENS` (output token budget) |
| `CC_MINI_CONTEXT_WINDOW` | Model context window size (e.g. `32768`, `200000`) |
| `CC_MINI_SAFETY_MARGIN_TOKENS` | Reserved safety margin (default varies by runtime profile) |
| `CC_MINI_AUTO_COMPACT` | Enable automatic context compaction when approaching limits |
| `CC_MINI_AUTO_APPROVE` | Auto-approve all tool permissions (dangerous; use with care) |
| `CC_MINI_EFFORT` | Reasoning effort: `low`, `medium`, `high` |
| `CC_MINI_MODE` | `standard` or `wiki_strict` |
| `CC_MINI_BUDDY_MODEL` | Model for companion reactions |
| `CC_MINI_COORDINATOR` | Set to `1` to enable coordinator mode |

### CLI Flags

```bash
cc-mini \
  --provider anthropic \
  --model claude-sonnet-4-6 \
  --max-tokens 32000 \
  --effort medium \
  --mode wiki_strict \
  --auto-approve \
  --coordinator
```

### TOML Config Files

Loaded in order (later overrides earlier):

1. `~/.config/cc-mini/config.toml`
2. `.cc-mini.toml` in current working directory

Example `.cc-mini.toml` with N-context runtime settings:

```toml
provider = "openai"
model = "gpt-4.1"
max_tokens = 16384

[context]
window = 32768
max_output_tokens = 2048
safety_margin_tokens = 2048
```

### Local Models (MLX / OMLX / OpenAI-Compatible)

Local models use the `openai` provider with a custom `base_url`:

```bash
cc-mini \
  --provider openai \
  --base-url http://localhost:8080/v1 \
  --model mlx-community/Mistral-7B-Instruct-v0.2-MLX \
  --max-tokens 32000
```

- `--max-tokens` is the **output token budget**, not the full context window.
- For 32K local models, `32000` is the safe default (leaves ~768 tokens for prompt overhead).
- Use `/model-health` inside the REPL to verify your endpoint.

See [`docs/local-models.md`](docs/local-models.md) for full setup, troubleshooting, and health-check details.

---

## Architecture

### Core Components

| Module | File | Purpose |
|--------|------|---------|
| **Entry / REPL** | `src/core/main.py` | CLI argument parsing, prompt_toolkit REPL, command dispatch |
| **Engine** | `src/core/engine.py` | Streaming API loop, tool execution, retry logic |
| **LLM Client** | `src/core/llm.py` | Anthropic + OpenAI-compatible provider abstraction |
| **Config** | `src/core/config.py` | Layered config: CLI args > env vars > TOML files |
| **Context** | `src/core/context.py` | System prompt builder (includes optional `CLAUDE.md` from cwd) |
| **Commands** | `src/core/commands.py` | Slash command parsing and handling |
| **Session** | `src/core/session.py` | SQLite-based session persistence |
| **Compact** | `src/core/compact.py` | Context compression when approaching token limits |
| **Token Budget** | `src/core/token_budget.py` | Token usage tracking and budget decisions |
| **Permissions** | `src/core/permissions.py` | Auto-approve read tools, confirm write/bash tools |

### Tool System (`src/core/tools/`)

All tools inherit from `Tool` base class. Read-only tools are auto-approved; write tools require confirmation.

**Standard tools:** `Read`, `Edit`, `Write`, `Glob`, `Grep`, `Bash`, `AskUser`

**Coordinator tools:** `Agent`, `SendMessage`, `TaskStop`

**Wiki-Strict tools:** minimal analysis chain in phase 1; `ASTRead` and stricter edit/verify tooling are reserved for later phase hardening

### Subsystems

| Subsystem | Directory | Purpose |
|-----------|-----------|---------|
| **Buddy** | `src/core/buddy/` | AI companion with personality, mood, and minigame |
| **Sandbox** | `src/core/sandbox/` | Bubblewrap isolation for bash commands |
| **Wiki** | `src/core/wiki/` | Wiki-strict analysis lifecycle in phase 1; later phases add reconcile, archive, lint, and maintenance |
| **Knowledge** | `src/core/knowledge/` | Ingestion, file watching, dehydration |
| **Skills** | `src/core/skills.py`, `src/core/skills_bundled.py` | One-command workflows (`/review`, `/commit`, `/test`) |
| **Memory** | `src/core/memory.py` | KAIROS cross-session memory with auto-consolidation |
| **Coordinator** | `src/core/coordinator.py`, `src/core/worker_manager.py` | Background worker system with task-kind-aware launches |

---

## Tools

### Standard Tools

| Tool | Description | Permission |
|------|-------------|------------|
| `Read` | Read file contents | auto-approved |
| `Glob` | Find files by pattern | auto-approved |
| `Grep` | Search file contents | auto-approved |
| `Edit` | Edit file (string replacement) | requires confirmation |
| `Write` | Write/create file | requires confirmation |
| `Bash` | Run shell command | requires confirmation |
| `AskUser` | Ask user a question | interactive |

---

## Slash Commands

### Core
然后检查：

```bash

| Command | Description |
|---------|-------------|
| `/help` | Show all available commands |
| `/compact` | Compress conversation context |
| `/resume` | Resume a past session |
| `/history` | List saved sessions |
| `/clear` | Clear conversation, start new seqssion |
| `/skills` | List all available skills |

### Buddy

| Command | Description |
|---------|-------------|
| `/buddy` | Hatch or show companion |
| `/buddy pet` | Pet your companion |
| `/buddy mood` | Check companion's mood |
| `/buddy mute` / `/buddy unmute` | Toggle reactions |

### Wiki-Strict

| Command | Description |
|---------|-------------|
| `/scan` | Scan files for wiki entities |
| `/digest` | Digest files into wiki format |
| `/digest --changed` | Digest only changed files |
| `/prime` | Generate TaskPack from digest |
| `/plan` | Create structured patch plan |
| `/reconcile` | View-only reconcile projection from semantic artifacts |
| `/maintenance` | View-only maintenance projection from semantic artifacts |

### General Agent

| Command | Description |
|---------|-------------|
| `/task` | Intake a broader task request and keep the first routing pass coding-adjacent when possible |

Phase 5 starts widening task intake in a bounded way:

- `/task` accepts broader requests without assuming they are code changes.
- Worker launches can carry a `task_kind` hint: `coding`, `research`, or `general`.
- The first wave still prefers coding-adjacent work before broader non-coding expansion.

Phase 1 keeps this area intentionally small:

- `scan`
- `prime`
- `plan`
- structured output for Goal Stack, TaskPack, and EditSpec

The broader patch / post-edit / maintenance lifecycle is reserved for later-phase hardening and is intentionally excluded from the Phase 1 startup path.
The later-phase `/reconcile` and `/maintenance` commands are view-only projections: they summarize derived/manual artifact state and do not execute file mutations.
If you see deeper wiki commands in the codebase, treat them as later-stage surfaces unless this phase 1 document explicitly includes them.

### Skills

| Command | Description |
|---------|-------------|
| `/review` | Code review (read-only) |
| `/close` | Draft a milestone closeout; commit happens only after manual `/close confirm` |
| `/milestone-review` | Read-only review of the latest closeout record |
| `/simplify` | Review and fix code |
| `/commit` | Git commit with generated message |
| `/test` | Run tests and analyze failures |

The closure flow is intentionally split: `/close` drafts the record, `/close confirm` is the manual confirmation step before commit, and `/milestone-review` only reads the latest closeout state.

Type `/` to see autocomplete suggestions.

---

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Skip integration tests (sandbox/bwrap)
pytest tests/ -v -k "not integration"

# Run specific test file
pytest tests/test_engine.py -v

# Run specific test
pytest tests/test_engine.py::test_name -v
```

---

## Development

### Local Setup

```bash
git clone <repo>
cd cc-mini
pip install -e ".[dev]"
```

### Running from Source

```bash
export PYTHONPATH=src
python -m core.main
```

### Running in Wiki-Strict Mode

```bash
export CC_MINI_MODE=wiki_strict
export PYTHONPATH=src
python -m core.main
```

---

## Migration

If you are upgrading from an earlier version that used `wiki_strict` with `.cc-mini/`, `memory-bank/`, or the full wiki lifecycle, see the migration guide:

- [`docs/migration-context-bounded-workflow.md`](docs/migration-context-bounded-workflow.md)

## License

MIT

