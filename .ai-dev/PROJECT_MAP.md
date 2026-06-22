# Project Map

## Purpose

This file is a compact navigation map for cc-mini.

It is not a full wiki. Use it to quickly locate the right area before reading source files.

## Repository Shape

Core project files:

- `src/core/` — product source code
- `tests/` — test suite
- `docs/` — user-facing or durable documentation
- `assets/` — static assets
- `pyproject.toml` — package metadata, dependencies, CLI entry
- `install.sh` — installation helper
- `README.md` — project overview
- `AGENTS.md` — coding-agent workflow rules
- `.ai-dev/` — context-bounded development workflow files

Ignored local workflow state:

- `.ai-dev/tasks/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`
- `.codegraph/`
- `.codebase-memory/`

## Product Summary

cc-mini is an AI coding assistant CLI/harness.

It implements a Claude Code-like workflow:

- interactive CLI / REPL
- agentic tool loop
- tool permission checks
- session persistence
- model/provider abstraction
- context and token budget management
- checkpointing
- compact/dehydration support
- skills support
- wiki-strict mode for smaller context windows
- sandbox and safety layers

The current development direction is to make cc-mini work reliably with small-context models by using context-bounded development.

## Main Entry Points

### CLI / REPL

Path:

- `src/core/main.py`

Responsibilities:

- parse CLI arguments
- initialize configuration
- start interactive REPL
- create `Engine`
- wire session, permissions, sandbox, worker manager
- dispatch slash commands
- handle runtime lifecycle behavior

Use this area when changing:

- command-line UX
- REPL behavior
- startup/shutdown
- slash command routing
- interactive session behavior

### Engine

Path:

- `src/core/engine.py`

Responsibilities:

- model/tool loop
- streaming response handling
- tool call execution
- message normalization
- token budget checks
- dehydration/compact/checkpoint integration
- retry/error handling

Use this area when changing:

- model call loop
- tool execution order
- message handling
- context budget behavior
- streaming behavior
- checkpoint triggers

### LLM Provider

Path:

- `src/core/llm.py`

Responsibilities:

- provider abstraction
- Anthropic/OpenAI-compatible API calling
- streaming
- error classification

Use this area when changing:

- provider support
- request/response format
- model configuration
- API compatibility

### Configuration

Path:

- `src/core/config.py`

Responsibilities:

- load config from CLI/env/TOML
- define runtime configuration
- normalize configuration values

Use this area when changing:

- config options
- environment variable behavior
- model defaults
- local config loading

### Commands

Path:

- `src/core/commands.py`

Responsibilities:

- slash command definitions and dispatch support

Use this area when changing:

- slash commands
- command routing
- command metadata

## Key Subsystems

### Tools

Directory:

- `src/core/tools/`

Likely responsibilities:

- file read/write/edit
- bash execution
- grep/glob
- AST read
- plan-mode tools
- error handling tools
- ask-user tools
- agent tools

Important tool concepts:

- read-only tools can be auto-approved
- write tools should require permission
- strict edit tools may be used in constrained modes

Use this area when changing:

- tool schemas
- tool permissions
- file editing behavior
- search behavior
- bash execution
- plan-mode tool access

### Permissions

Path:

- `src/core/permissions.py`

Responsibilities:

- approve/deny tool actions
- enforce human confirmation for risky actions
- coordinate safety checks

Use this area when changing:

- approval policy
- write confirmation behavior
- trusted/untrusted commands
- tool safety

### Sandbox

Directory:

- `src/core/sandbox/`

Responsibilities:

- command sandboxing
- sandbox configuration
- safe command execution boundaries

Use this area when changing:

- subprocess isolation
- allowed command behavior
- sandbox config
- integration tests around shell execution

### Session

Path:

- `src/core/session.py`

Responsibilities:

- persistent session storage
- conversation history
- resume behavior

Use this area when changing:

- session serialization
- JSONL storage
- resume behavior
- history boundaries

### Memory / Dream / KAIROS

Path:

- `src/core/memory.py`

Responsibilities:

- cross-session memory
- background reflection/dream behavior
- session summaries or long-term memory behavior

Use this area when changing:

- memory generation
- background summarization
- dream-mode isolation
- cross-session recall

### Token Budget

Path:

- `src/core/token_budget.py`

Responsibilities:

- token estimation
- budget thresholds
- compact/checkpoint decisions

Use this area when changing:

- 32k/64k/128k policies
- model-aware context windows
- token counting
- output reservation

### Compact

Path:

- `src/core/compact.py`

Responsibilities:

- context compaction
- summarization behavior
- compact thresholds

Use this area when changing:

- compression strategy
- no-compact mode
- summary quality
- model-specific compaction behavior

### Dehydration

Paths:

- `src/core/dehydration.py`
- `src/core/knowledge/dehydrator.py`

Responsibilities:

- reduce old tool results/messages
- save smaller runtime state
- support context recovery

Use this area when changing:

- message shrinking
- checkpoint payload
- runtime snapshot behavior

### Checkpoint

Path:

- `src/core/checkpoint.py`

Responsibilities:

- save recoverable runtime state
- restore from interrupted work

Use this area when changing:

- rollback/resume support
- checkpoint metadata
- step-level recovery

### Worker Manager

Path:

- `src/core/worker_manager.py`

Responsibilities:

- background or delegated work
- worker lifecycle

Use this area when changing:

- sub-agent/worker behavior
- parallel task execution
- background job management

### Skills

Paths:

- `src/core/skills.py`
- `src/core/skills_bundled.py`

Responsibilities:

- discover/load/register skills
- bundled skill behavior

Use this area when changing:

- skill loading
- custom skill paths
- bundled workflows
- skill metadata

### Buddy

Directory:

- `src/core/buddy/`

Responsibilities:

- companion/personality feature
- buddy state/mood/storage

Use this area when changing:

- buddy interactions
- buddy persistence
- companion behavior

### Wiki / Wiki-Strict

Directories:

- `src/core/wiki/`
- `src/core/knowledge/`

Responsibilities:

- wiki-strict workflow
- taskpack/edit spec behavior
- archive/reconcile/lint/maintenance
- AST or knowledge ingestion
- file watcher / wiki updates

Use this area when changing:

- wiki-strict mode
- low-context workflow
- taskpack generation
- strict patch verification
- knowledge ingestion
- codebase maps

## Tests

Main test directory:

- `tests/`

Notable test areas:

- `tests/test_engine.py`
- `tests/test_main.py`
- `tests/test_commands.py`
- `tests/test_context.py`
- `tests/test_config.py`
- `tests/test_permissions.py`
- `tests/test_tools.py`
- `tests/test_skills.py`
- `tests/test_wiki_phase1.py`
- `tests/test_wiki_phase3.py`
- `tests/test_wiki_phase6.py`
- `tests/core/`

Use targeted tests first. Avoid running broad suites unless needed.

## Risk Areas

Treat these areas as high-risk:

- `src/core/main.py` — central REPL and lifecycle wiring
- `src/core/engine.py` — tool loop, model loop, streaming, budget integration
- `src/core/llm.py` — provider compatibility
- `src/core/permissions.py` — safety boundary
- `src/core/sandbox/` — command execution safety
- `src/core/token_budget.py` — context-window correctness
- `src/core/compact.py` — expensive or lossy summarization
- `src/core/session.py` — persistence/resume correctness
- `src/core/memory.py` — background memory/dream isolation
- `src/core/wiki/` — wiki-strict lifecycle behavior
- `src/core/tools/` — tool schemas and file mutation behavior

For these areas, require:

- narrow task scope
- context pack
- targeted tests
- review rollback
- work log

## Recommended Development Order

For workflow/product changes, prefer this order:

1. Update or create workflow task.
2. Run surface-search to find anchors.
3. Use code-intel to inspect exact symbols.
4. Build a context pack.
5. Implement one small task.
6. Run map-sync after code changes.
7. Run test-gate.
8. Run fresh-review or review-rollback.
9. Commit or rollback.
10. Write work-log.

## Common Starting Anchors

For CLI command changes:

- `src/core/main.py`
- `src/core/commands.py`
- `tests/test_main.py`
- `tests/test_commands.py`

For tool changes:

- `src/core/tools/`
- `src/core/permissions.py`
- `tests/test_tools.py`
- `tests/test_permissions.py`

For token/context behavior:

- `src/core/token_budget.py`
- `src/core/context.py`
- `src/core/compact.py`
- `src/core/dehydration.py`
- `tests/test_context.py`
- `tests/core/test_token_budget.py`

For wiki-strict behavior:

- `src/core/wiki/`
- `src/core/knowledge/`
- `tests/test_wiki_phase1.py`
- `tests/test_wiki_phase3.py`
- `tests/test_wiki_phase6.py`

For skills behavior:

- `src/core/skills.py`
- `src/core/skills_bundled.py`
- `tests/test_skills.py`

For session/memory behavior:

- `src/core/session.py`
- `src/core/memory.py`
- `tests/test_session_mode.py`
- `tests/test_maintenance.py`

## CodeGraph Starter Queries

Use CodeGraph after `codegraph init`.

Examples:

```bash
codegraph status
codegraph files
codegraph query "Engine"
codegraph query "Tool"
codegraph query "token_budget"
codegraph query "wiki"
codegraph query "skills"
codegraph query "commands"
codegraph callers "Engine"
codegraph callees "Engine"
codegraph impact "Engine"
```

If the task has no clear symbol yet, run `surface-search` before `code-intel`.

## Do Not Use This File For

Do not use this file as:

- a complete architecture spec
- a generated wiki
- a replacement for CodeGraph
- a place to paste logs
- a work log
- a task file

Keep it compact and update only when high-level project structure changes.