# Codebase Structure

**Analysis Date:** 2026-04-18

## Directory Layout

```
[project-root]/
├── src/core/              # Main source code
│   ├── tools/             # LLM tool implementations
│   ├── sandbox/           # Bubblewrap sandbox subsystem
│   ├── wiki/              # Wiki-strict mode subsystems
│   ├── knowledge/         # Document ingestion and dehydration
│   └── buddy/             # Companion pet and minigame
│       └── poke_game/     # Roguelike idle adventure
├── tests/                 # pytest test suite
│   └── core/              # Tests for core submodules
├── docs/                  # Documentation (non-wiki)
├── .github/workflows/     # CI configuration
├── pyproject.toml         # Project metadata and dependencies
└── .claude/               # Project instructions for Claude Code
    └── CLAUDE.md
```

## Directory Purposes

**`src/core/`:**
- Purpose: All runtime source code
- Contains: Python modules for REPL, engine, LLM client, tools, config, context, commands, session, memory, skills, sandbox, wiki, knowledge, buddy
- Key files: `main.py`, `engine.py`, `llm.py`, `config.py`, `context.py`, `commands.py`

**`src/core/tools/`:**
- Purpose: Tool implementations callable by the LLM
- Contains: One file per tool plus `base.py` abstract class
- Key files: `base.py`, `file_read.py`, `file_edit.py`, `file_edit_strict.py`, `file_write.py`, `bash.py`, `glob_tool.py`, `grep_tool.py`, `ask_user.py`, `agent.py`, `ast_read.py`, `plan_tools.py`

**`src/core/sandbox/`:**
- Purpose: Bubblewrap-based command isolation
- Contains: Manager, config, dependency checker, wrapper, command matcher
- Key files: `manager.py`, `config.py`, `checker.py`, `wrapper.py`, `command_matcher.py`

**`src/core/wiki/`:**
- Purpose: Wiki-strict mode structured workflow
- Contains: Task planning, reconciliation, archiving, lint, maintenance, post-edit guard, target identity
- Key files: `taskpack.py`, `post_edit_guard.py`, `target_identity.py`, `reconcile.py`, `archive.py`

**`src/core/knowledge/`:**
- Purpose: Document ingestion, file watching, message dehydration
- Contains: Ingester, watcher, dehydrator
- Key files: `ingester.py`, `watcher.py`, `dehydrator.py`

**`src/core/buddy/`:**
- Purpose: Companion pet system
- Contains: Companion logic, mood, animator, observer, storage, render, sprites, commands, and roguelike minigame
- Key files: `companion.py`, `animator.py`, `mood.py`, `observer.py`, `storage.py`

**`tests/`:**
- Purpose: pytest test suite
- Contains: Top-level tests and `core/` subdirectory tests
- Key files: `conftest.py`, `test_engine.py`, `test_tools.py`, `test_config.py`, `test_main.py`

**`docs/`:**
- Purpose: Markdown documentation
- Contains: `buddy.md`, `configuration.md`, `coordinator.md`, `memory.md`, `sandbox.md`, `skills.md`

## Key File Locations

**Entry Points:**
- `src/core/main.py`: CLI entry point and REPL loop
- `pyproject.toml`: Defines `cc-mini = "core.main:main"` console script

**Configuration:**
- `pyproject.toml`: Build system, dependencies, pytest settings
- `src/core/config.py`: Runtime config loading (CLI > env > TOML)

**Core Logic:**
- `src/core/engine.py`: Streaming API loop and tool execution orchestration
- `src/core/llm.py`: Anthropic/OpenAI client abstraction
- `src/core/context.py`: System prompt builder
- `src/core/compact.py`: Context compression service
- `src/core/token_budget.py`: Token budget manager with thresholds
- `src/core/checkpoint.py`: Checkpoint manager for session recovery

**Tool Definitions:**
- `src/core/tools/base.py`: Abstract `Tool` base class
- `src/core/tools/file_read.py`: Read files
- `src/core/tools/file_edit.py`: Edit files (standard mode)
- `src/core/tools/file_edit_strict.py`: Edit files (wiki-strict mode)
- `src/core/tools/file_write.py`: Write files
- `src/core/tools/bash.py`: Execute shell commands
- `src/core/tools/glob_tool.py`: File pattern search
- `src/core/tools/grep_tool.py`: Content search
- `src/core/tools/ask_user.py`: Ask user questions
- `src/core/tools/agent.py`: Spawn background workers
- `src/core/tools/ast_read.py`: AST-based code reading (wiki-strict)
- `src/core/tools/plan_tools.py`: Enter/exit plan mode

**Testing:**
- `tests/conftest.py`: Shared pytest fixtures
- `tests/test_engine.py`: Engine loop tests
- `tests/test_tools.py`: Tool execution tests
- `tests/test_config.py`: Config loading tests
- `tests/test_main.py`: REPL and main entry tests
- `tests/core/test_compact_runtime.py`: Compaction runtime tests
- `tests/core/test_token_budget.py`: Token budget tests
- `tests/core/test_dehydration.py`: Dehydration tests

## Naming Conventions

**Files:**
- Modules: `snake_case.py` (e.g., `file_read.py`, `token_budget.py`)
- Test files: `test_<module>.py` (e.g., `test_engine.py`)
- Tool files: `<descriptive>_tool.py` or `<noun>_tool.py` (e.g., `glob_tool.py`, `bash.py`)

**Directories:**
- Package directories: `snake_case` (e.g., `wiki/`, `knowledge/`, `poke_game/`)
- Test subdirectories mirror source structure: `tests/core/` for `src/core/`

**Classes:**
- PascalCase (e.g., `Engine`, `LLMClient`, `TokenBudgetManager`, `CompactService`)

**Functions:**
- snake_case (e.g., `build_system_prompt()`, `estimate_tokens()`)
- Private helpers: leading underscore (e.g., `_split_recent()`, `_strip_media()`)

## Where to Add New Code

**New Feature (non-tool):**
- Primary code: `src/core/<feature_module>.py`
- Tests: `tests/test_<feature>.py` or `tests/core/test_<feature>.py`

**New Tool:**
- Implementation: `src/core/tools/<descriptive_name>.py`
- Register in: `src/core/main.py` inside `_build_base_tools()` or `_build_tools_for_mode()`
- Tests: `tests/test_tools.py` (add test cases to existing file)

**New Wiki-Strict Subsystem:**
- Implementation: `src/core/wiki/<subsystem>.py`
- Register command handler in: `src/core/commands.py` (`_COMMAND_TABLE`)
- Tests: `tests/core/test_<subsystem>.py`

**New Skill:**
- Bundled skill: register in `src/core/skills_bundled.py`
- Project skill: create `SKILL.md` under `{cwd}/.cc-mini/skills/<name>/`
- User skill: create `SKILL.md` under `~/.cc-mini/skills/<name>/`

**Utilities:**
- Shared helpers: add to existing module (e.g., `src/core/config.py` for config helpers)
- Cross-cutting: consider `src/core/<concern>.py` (e.g., `cost_tracker.py`)

## Special Directories

**`.claude/`:**
- Purpose: Project instructions for Claude Code
- Contains: `CLAUDE.md`
- Generated: No
- Committed: Yes

**`.github/workflows/`:**
- Purpose: CI/CD configuration
- Contains: `wiki-lint.yml`
- Generated: No
- Committed: Yes

**`src/core/buddy/poke_game/`:**
- Purpose: Roguelike idle adventure minigame
- Contains: State, world, battle, render, narrator, persistence, badges, events, lockfile
- Generated: No
- Committed: Yes

---

*Structure analysis: 2026-04-18*
