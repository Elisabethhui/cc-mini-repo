# Project Map

## Purpose

Compact navigation map for cc-mini. This is not a full wiki.

## Repository Shape

- `src/core/` product source
- `tests/` test suite
- `docs/` durable docs
- `assets/` static assets
- `pyproject.toml` package metadata
- `install.sh` installer
- `AGENTS.md` agent rules
- `.ai-dev/` context-bounded workflow files

## Main Anchors

- CLI/REPL: `src/core/main.py`
- Engine/tool loop: `src/core/engine.py`
- Provider abstraction: `src/core/llm.py`
- Config: `src/core/config.py`
- Commands: `src/core/commands.py`
- Tools: `src/core/tools/`
- Permissions: `src/core/permissions.py`
- Sandbox: `src/core/sandbox/`
- Session: `src/core/session.py`
- Memory: `src/core/memory.py`
- Token budget: `src/core/token_budget.py`
- Compact: `src/core/compact.py`
- Skills: `src/core/skills.py`, `src/core/skills_bundled.py`
- Wiki strict: `src/core/wiki/`, `src/core/knowledge/`

## Risk Areas

High-risk areas include `main.py`, `engine.py`, `llm.py`, `permissions.py`, `sandbox/`, `token_budget.py`, `compact.py`, `session.py`, `memory.py`, `wiki/`, and `tools/`.

## Starting Anchors

- CLI command changes: `src/core/main.py`, `src/core/commands.py`, `tests/test_main.py`, `tests/test_commands.py`
- Tool changes: `src/core/tools/`, `src/core/permissions.py`, `tests/test_tools.py`
- Token/context: `src/core/token_budget.py`, `src/core/context.py`, `src/core/compact.py`, `src/core/dehydration.py`
- Wiki strict: `src/core/wiki/`, `src/core/knowledge/`, `tests/test_wiki_phase*.py`
