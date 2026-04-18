# cc-mini Codebase Structure

## Repository Root Layout

```
cc-mini-repo/
├── src/core/                    # Main Python source code
│   ├── main.py                  # CLI entry point and REPL (1393 lines)
│   ├── engine.py                # Streaming API loop and tool orchestration (610 lines)
│   ├── llm.py                   # Anthropic/OpenAI provider abstraction (612 lines)
│   ├── context.py               # System prompt construction (317 lines)
│   ├── config.py                # Configuration loading: CLI > env > TOML (355 lines)
│   ├── commands.py              # Slash command parsing and dispatch (969 lines)
│   ├── session.py               # JSONL session persistence (229 lines)
│   ├── compact.py               # Context compression via summarization (345 lines)
│   ├── permissions.py           # Tool permission checker with interactive prompts (131 lines)
│   ├── coordinator.py           # Coordinator mode and worker system prompts (341 lines)
│   ├── worker_manager.py        # Background worker thread management (236 lines)
│   ├── plan.py                  # Plan mode lifecycle manager (179 lines)
│   ├── flow_state.py            # Wiki-strict 4-state machine (38 lines)
│   ├── token_budget.py          # Token budget thresholds and decisions (145 lines)
│   ├── checkpoint.py            # Checkpoint manifest and report writer (139 lines)
│   ├── dehydration.py           # Message dehydration for context saving (109 lines)
│   ├── memory.py                # KAIROS cross-session memory system (392 lines)
│   ├── cost_tracker.py          # Token usage and cost tracking (227 lines)
│   ├── skills.py                # SKILL.md discovery and execution (291 lines)
│   ├── skills_bundled.py        # Built-in skill registrations (223 lines)
│   ├── _keylistener.py          # ESC key listener for turn cancellation (235 lines)
│   ├── tools/                   # Tool implementations
│   │   ├── __init__.py
│   │   ├── base.py              # Tool / ToolResult abstract base (41 lines)
│   │   ├── file_read.py         # FileReadTool (58 lines)
│   │   ├── file_edit.py         # FileEditTool (standard) (66 lines)
│   │   ├── file_edit_strict.py  # FileEditTool (wiki-strict with backup/rollback) (155 lines)
│   │   ├── file_write.py        # FileWriteTool (42 lines)
│   │   ├── bash.py              # BashTool with sandbox integration (107 lines)
│   │   ├── glob_tool.py         # GlobTool (44 lines)
│   │   ├── grep_tool.py         # GrepTool (102 lines)
│   │   ├── ast_read.py          # ASTReadTool (Python AST-based reading) (187 lines)
│   │   ├── ask_user.py          # AskUserQuestionTool interactive selector (409 lines)
│   │   ├── agent.py             # AgentTool, SendMessageTool, TaskStopTool (100 lines)
│   │   ├── plan_tools.py        # EnterPlanModeTool, ExitPlanModeTool (122 lines)
│   │   ├── reanchor.py          # Reanchor tool (204 lines)
│   │   └── error_handler.py     # Tool error handling (225 lines)
│   ├── wiki/                    # Wiki-strict mode subsystems
│   │   ├── __init__.py
│   │   ├── taskpack.py          # TaskPack, EditSpec, GoalStack, TaskPackManager (375 lines)
│   │   ├── target_identity.py   # TargetResolver, TargetIdentity, disambiguation (418 lines)
│   │   ├── post_edit_guard.py   # Patch impact analysis, completion state (509 lines)
│   │   ├── archive.py           # ArchiveEngine for old snapshots/taskpacks (206 lines)
│   │   ├── reconcile.py         # ReconcileEngine for stale entities (259 lines)
│   │   ├── maintenance.py       # MaintenanceEngine lifecycle management (304 lines)
│   │   ├── lint.py              # Wiki structure health checks (324 lines)
│   │   └── query_archive.py     # Query archived items (192 lines)
│   ├── knowledge/               # Knowledge ingestion system
│   │   ├── __init__.py
│   │   ├── ingester.py          # WikiIngester: AST parsing, entity generation (340 lines)
│   │   ├── watcher.py           # Filesystem watcher for incremental updates (114 lines)
│   │   └── dehydrator.py        # MinimalDehydrator for context compression (170 lines)
│   ├── sandbox/                 # Bubblewrap sandbox subsystem
│   │   ├── __init__.py
│   │   ├── manager.py           # SandboxManager unified interface (125 lines)
│   │   ├── config.py            # SandboxConfig dataclass, TOML I/O (251 lines)
│   │   ├── wrapper.py           # bwrap argument builder (143 lines)
│   │   ├── checker.py           # Dependency validation (86 lines)
│   │   └── command_matcher.py   # Excluded command pattern matching (101 lines)
│   └── buddy/                   # Companion pet system
│       ├── __init__.py
│       ├── companion.py         # Deterministic companion generation (221 lines)
│       ├── animator.py          # Real-time sprite animation (259 lines)
│       ├── observer.py          # Background reaction generator (165 lines)
│       ├── mood.py              # Rule-based mood engine (147 lines)
│       ├── storage.py           # JSON persistence (282 lines)
│       ├── sprites.py           # ASCII sprite rendering (540 lines)
│       ├── render.py            # Rendering helpers (318 lines)
│       ├── types.py             # Companion dataclasses and constants (180 lines)
│       ├── prompt.py            # Companion system prompt text (27 lines)
│       ├── commands.py          # Buddy slash command handlers (351 lines)
│       └── poke_game/           # Idle Adventure roguelike
│           ├── __init__.py
│           ├── loop.py          # Game loop (423 lines)
│           ├── world.py         # World generation (472 lines)
│           ├── battle.py        # Battle system (235 lines)
│           ├── narrator.py      # Story narration (384 lines)
│           ├── render.py        # Game rendering (391 lines)
│           ├── state.py         # Game state (112 lines)
│           ├── types.py         # Game type definitions (190 lines)
│           ├── events.py        # Event system (143 lines)
│           ├── badges.py        # Achievement system (205 lines)
│           ├── commands.py      # Game commands (200 lines)
│           ├── persistence.py   # Save/load (84 lines)
│           └── lockfile.py      # Save file locking (85 lines)
├── tests/                       # pytest test suite
├── docs/wiki/                   # Wiki pages (index, current-status, log, schema)
│   ├── index.md
│   ├── current-status.md
│   ├── log.md
│   └── SCHEMA.md
├── memory-bank/                 # Long-term rules, plans, progress, architecture
├── scripts/                     # Maintenance and validation scripts
│   ├── version_check.py
│   ├── wiki_check.py
│   ├── raw_manifest_check.py
│   ├── untracked_raw_check.py
│   ├── stale_report.py
│   └── provenance_check.py
├── manifests/                   # Raw source manifests
├── .cc-mini/                    # Runtime wiki workspace
│   ├── wiki/
│   │   ├── entities/            # Generated entity markdown files
│   │   ├── taskpacks/           # TaskPack JSON files
│   │   ├── reports/             # Impact summaries, deferred issues, micro-forks
│   │   ├── snapshots/           # Context snapshots
│   │   └── archive/             # Archived items
│   └── skills/                  # Project-level skills
├── pyproject.toml               # Package metadata and dependencies
└── README.md
```

---

## Directory Conventions

### Source Code (`src/core/`)

| Convention | Description |
|------------|-------------|
| `*.py` at root level | Core framework modules (engine, config, session, etc.) |
| `tools/` | All tool implementations — one file per tool |
| `wiki/` | Wiki-strict mode subsystems — task planning, identity, guards |
| `knowledge/` | Knowledge ingestion — AST parsing, file watching, dehydration |
| `sandbox/` | Bubblewrap integration — config, wrapping, dependency checks |
| `buddy/` | Companion system — deterministic generation, animation, mood |
| `buddy/poke_game/` | Roguelike mini-game — self-contained sub-package |

### Naming Conventions

| Pattern | Used For | Example |
|---------|----------|---------|
| `*_tool.py` | Tool implementations | `file_read.py`, `bash.py` |
| `*_manager.py` | Lifecycle managers | `worker_manager.py`, `sandbox/manager.py` |
| `*_engine.py` / `*Engine` class | Processing engines | `engine.py`, `wiki/archive.py` |
| `*_checker.py` / `*Checker` class | Validation | `permissions.py`, `sandbox/checker.py` |
| `*_store.py` / `*Store` class | Persistence | `session.py`, `wiki/target_identity.py` |
| `*_service.py` / `*Service` class | Services | `compact.py` |
| `test_*.py` | Test files (in `tests/`) | `test_engine.py` |
| `SKILL.md` | Skill definitions (in `.cc-mini/skills/`) | — |

### Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `config.toml` | `~/.config/cc-mini/` | Global user configuration |
| `.cc-mini.toml` | Project root | Project-local configuration |
| `CLAUDE.md` | Project root | Project instructions for Claude |
| `.cc-mini/` | Project root | Runtime wiki workspace (entities, taskpacks, snapshots) |

### Data Storage

| Directory | Location | Contents |
|-----------|----------|----------|
| `~/.mini-claude/sessions/` | User home | JSONL conversation history per project |
| `~/.mini-claude/memory/` | User home | KAIROS memory (daily logs, topic files, MEMORY.md) |
| `~/.cc-mini/skills/` | User home | User-level SKILL.md definitions |
| `{project}/.cc-mini/skills/` | Project root | Project-level SKILL.md definitions |
| `{project}/.cc-mini/wiki/` | Project root | Generated wiki entities, taskpacks, reports |
| `~/.claude/plans/` | User home | Plan mode plan files |

---

## Key File Locations

### Entry Points

| File | Role | Lines |
|------|------|-------|
| `src/core/main.py` | CLI argument parsing, REPL loop, tool construction, mode initialization | 1393 |

### Core Framework

| File | Role | Lines |
|------|------|-------|
| `src/core/engine.py` | Streaming API loop, tool dispatch, retry logic, token budget integration | 610 |
| `src/core/llm.py` | Anthropic/OpenAI SDK abstraction, content block normalization | 612 |
| `src/core/context.py` | System prompt assembly (static + dynamic sections) | 317 |
| `src/core/config.py` | Configuration hierarchy: CLI args > environment > TOML files | 355 |
| `src/core/commands.py` | Slash command parsing (`/help`, `/compact`, `/resume`, `/plan`, etc.) | 969 |

### Data and State

| File | Role | Lines |
|------|------|-------|
| `src/core/session.py` | JSONL message persistence, session listing and loading | 229 |
| `src/core/compact.py` | Context compression: summarize old messages, preserve recent | 345 |
| `src/core/memory.py` | Daily logs, dream consolidation, MEMORY.md index | 392 |
| `src/core/checkpoint.py` | Checkpoint manifest writing for resume-from-checkpoint | 139 |
| `src/core/dehydration.py` | In-place message dehydration (tool result truncation) | 109 |

### Tools (by size)

| File | Role | Lines |
|------|------|-------|
| `src/core/tools/ask_user.py` | Interactive multi-choice question selector (prompt_toolkit) | 409 |
| `src/core/tools/error_handler.py` | Tool error classification and handling | 225 |
| `src/core/tools/reanchor.py` | Code reanchoring for patch application | 204 |
| `src/core/tools/ast_read.py` | AST-based file reading (symbol/span/anchor modes) | 187 |
| `src/core/tools/agent.py` | Agent, SendMessage, TaskStop tools for workers | 100 |
| `src/core/tools/bash.py` | Shell execution with sandbox integration | 107 |
| `src/core/tools/grep_tool.py` | Content search with regex | 102 |
| `src/core/tools/plan_tools.py` | Enter/Exit plan mode tools | 122 |
| `src/core/tools/file_edit_strict.py` | Wiki-strict edit with backup, preview, rollback | 155 |
| `src/core/tools/file_edit.py` | Standard exact-string edit | 66 |
| `src/core/tools/file_read.py` | File reading with line numbers | 58 |
| `src/core/tools/file_write.py` | File creation/overwriting | 42 |
| `src/core/tools/glob_tool.py` | File pattern matching | 44 |
| `src/core/tools/base.py` | Tool / ToolResult abstract base | 41 |

### Wiki-Strict Subsystems (by size)

| File | Role | Lines |
|------|------|-------|
| `src/core/wiki/post_edit_guard.py` | Patch impact analysis, completion state machine | 509 |
| `src/core/wiki/target_identity.py` | Target disambiguation for `/prime` command | 418 |
| `src/core/wiki/taskpack.py` | TaskPack, EditSpec, GoalStack, TaskPackManager | 375 |
| `src/core/wiki/lint.py` | Wiki structure health checks | 324 |
| `src/core/wiki/maintenance.py` | Lifecycle maintenance of snapshots/taskpacks | 304 |
| `src/core/wiki/reconcile.py` | Stale entity detection and recovery | 259 |
| `src/core/wiki/archive.py` | Automatic archiving with age thresholds | 206 |
| `src/core/wiki/query_archive.py` | Query archived items | 192 |

### Knowledge System

| File | Role | Lines |
|------|------|-------|
| `src/core/knowledge/ingester.py` | Workspace scanning, AST parsing, entity markdown generation | 340 |
| `src/core/knowledge/dehydrator.py` | Minimal dehydration for context compression | 170 |
| `src/core/knowledge/watcher.py` | Filesystem watcher for incremental re-ingestion | 114 |

### Sandbox

| File | Role | Lines |
|------|------|-------|
| `src/core/sandbox/config.py` | SandboxConfig dataclass, TOML load/save | 251 |
| `src/core/sandbox/manager.py` | SandboxManager unified interface | 125 |
| `src/core/sandbox/wrapper.py` | bwrap argument builder and command wrapper | 143 |
| `src/core/sandbox/command_matcher.py` | Excluded command pattern matching | 101 |
| `src/core/sandbox/checker.py` | Linux/bwrap/userns dependency validation | 86 |

### Buddy / Companion

| File | Role | Lines |
|------|------|-------|
| `src/core/buddy/sprites.py` | ASCII sprite rendering | 540 |
| `src/core/buddy/render.py` | Rendering helpers | 318 |
| `src/core/buddy/storage.py` | JSON persistence for companion data | 282 |
| `src/core/buddy/animator.py` | Real-time animation tick loop | 259 |
| `src/core/buddy/companion.py` | Deterministic companion generation | 221 |
| `src/core/buddy/poke_game/world.py` | Roguelike world generation | 472 |
| `src/core/buddy/poke_game/loop.py` | Game loop | 423 |
| `src/core/buddy/poke_game/narrator.py` | Story narration | 384 |
| `src/core/buddy/poke_game/render.py` | Game rendering | 391 |
| `src/core/buddy/commands.py` | Buddy slash command handlers | 351 |
| `src/core/buddy/observer.py` | Background reaction generator | 165 |
| `src/core/buddy/mood.py` | Rule-based mood engine | 147 |
| `src/core/buddy/poke_game/battle.py` | Battle system | 235 |
| `src/core/buddy/poke_game/badges.py` | Achievement system | 205 |
| `src/core/buddy/poke_game/commands.py` | Game commands | 200 |
| `src/core/buddy/poke_game/types.py` | Game type definitions | 190 |
| `src/core/buddy/types.py` | Companion dataclasses | 180 |
| `src/core/buddy/poke_game/events.py` | Event system | 143 |
| `src/core/buddy/poke_game/persistence.py` | Save/load | 84 |
| `src/core/buddy/poke_game/lockfile.py` | Save file locking | 85 |
| `src/core/buddy/poke_game/state.py` | Game state | 112 |
| `src/core/buddy/prompt.py` | Companion intro text | 27 |

### Other Key Modules

| File | Role | Lines |
|------|------|-------|
| `src/core/skills.py` | SKILL.md discovery, frontmatter parsing, execution | 291 |
| `src/core/skills_bundled.py` | Built-in skill registrations | 223 |
| `src/core/coordinator.py` | Coordinator mode prompt and state management | 341 |
| `src/core/worker_manager.py` | Background worker thread pool | 236 |
| `src/core/permissions.py` | Permission checking with interactive prompts | 131 |
| `src/core/token_budget.py` | Token budget thresholds and decision logic | 145 |
| `src/core/plan.py` | Plan mode lifecycle (enter/exit, tool restriction) | 179 |
| `src/core/flow_state.py` | Wiki-strict 4-state machine enum and prompt | 38 |
| `src/core/cost_tracker.py` | Token usage and cost tracking | 227 |
| `src/core/_keylistener.py` | ESC key listener for turn cancellation | 235 |

---

## Line Count Summary

### By Directory

| Directory | Files | Total Lines |
|-----------|-------|-------------|
| `src/core/` (root) | 19 | ~6,800 |
| `src/core/tools/` | 13 | ~1,700 |
| `src/core/wiki/` | 8 | ~2,600 |
| `src/core/knowledge/` | 3 | ~620 |
| `src/core/sandbox/` | 5 | ~710 |
| `src/core/buddy/` | 10 | ~2,600 |
| `src/core/buddy/poke_game/` | 10 | ~2,400 |
| **Total src/core/** | **68** | **~17,400** |

### Largest Files (top 15)

| Rank | File | Lines |
|------|------|-------|
| 1 | `src/core/main.py` | 1393 |
| 2 | `src/core/commands.py` | 969 |
| 3 | `src/core/buddy/sprites.py` | 540 |
| 4 | `src/core/wiki/post_edit_guard.py` | 509 |
| 5 | `src/core/buddy/poke_game/world.py` | 472 |
| 6 | `src/core/buddy/poke_game/loop.py` | 423 |
| 7 | `src/core/wiki/target_identity.py` | 418 |
| 8 | `src/core/tools/ask_user.py` | 409 |
| 9 | `src/core/buddy/poke_game/narrator.py` | 384 |
| 10 | `src/core/buddy/poke_game/render.py` | 391 |
| 11 | `src/core/memory.py` | 392 |
| 12 | `src/core/buddy/render.py` | 318 |
| 13 | `src/core/context.py` | 317 |
| 14 | `src/core/wiki/maintenance.py` | 304 |
| 15 | `src/core/skills.py` | 291 |

---

## Module Dependencies

### Import Graph (high-level)

```
main.py
  ├── engine.py
  │     ├── llm.py
  │     ├── tools.base
  │     ├── permissions.py
  │     ├── token_budget.py
  │     ├── dehydration.py
  │     └── checkpoint.py
  ├── context.py
  ├── config.py
  │     └── llm.py (defaults)
  ├── commands.py
  │     └── coordinator.py
  ├── session.py
  ├── compact.py
  │     └── llm.py
  ├── coordinator.py
  │     ├── config.py (RunMode)
  │     └── flow_state.py
  ├── worker_manager.py
  │     └── engine.py
  ├── plan.py
  │     └── tools.plan_tools
  ├── permissions.py
  │     ├── tools.base
  │     └── sandbox.manager
  ├── sandbox.manager
  │     ├── sandbox.config
  │     ├── sandbox.checker
  │     ├── sandbox.command_matcher
  │     └── sandbox.wrapper
  ├── skills.py
  ├── skills_bundled.py
  ├── memory.py
  ├── cost_tracker.py
  ├── buddy.companion
  ├── buddy.animator
  ├── buddy.observer
  ├── buddy.mood
  ├── buddy.storage
  ├── knowledge.ingester (wiki_strict mode)
  └── knowledge.watcher (wiki_strict mode)
```

### Wiki-Strict Mode Additional Imports

When `CC_MINI_MODE=wiki_strict`:
- `main.py` imports `knowledge.ingester` and `knowledge.watcher`
- `main.py` uses `ASTReadTool` instead of `FileReadTool`
- `main.py` uses `FileEditTool` from `file_edit_strict.py`
- `coordinator.py` injects `flow_state.py` prompt into system prompt
- `commands.py` routes `/plan` to `_cmd_plan_wiki` instead of `_cmd_plan`
