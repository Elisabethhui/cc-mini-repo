# AGENTS.md

## Core Rule

This repository uses context-bounded development. Prefer small, verifiable, reversible changes.

## File Boundary Rules

Every new file must be classified before creation:

- product code
- committed AI workflow file
- local task state
- generated output

Committed AI workflow files belong in `AGENTS.md`, `.ai-dev/skills/`, `.ai-dev/templates/`, `.ai-dev/design/`, or approved `.ai-dev/*.md` guide files.

Local task state belongs in ignored directories:

- `.ai-dev/tasks/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`

Do not commit `.codegraph/`, `.codebase-memory/`, or `CLAUDE.md` (all are gitignored).

## Code Reading Rules

Before reading large files:

1. Check the current task.
2. Use surface-search if there is no anchor.
3. Use code intelligence if available.
4. Use `rg` for exact search.
5. Read small snippets.
6. Read whole files only when necessary.

## Development Commands

- Install: `pip install -e ".[dev]"`
- Run from source: `PYTHONPATH=src python -m core.main`
- Run all tests: `pytest tests/ -v`
- Skip integration/sandbox tests: `pytest tests/ -v -k "not integration"`
- Run single test: `pytest tests/<file>.py::test_name -v`

## Architecture & Scope

- **Entry point**: `src/core/main.py` (installed as `cc-mini`)
- **Engine**: `src/core/engine.py`
- **Tools**: `src/core/tools/`
- Two runtime modes: `standard` (default interactive REPL) and `wiki_strict` (structured workflow with AST-based reading).
- **Phase 1 boundary**: The active product target is workspace bootstrap → scan → prime → structured planning output. Patch, post-edit, reconcile, archive, and maintenance are explicitly deferred to later phases. Do not treat later-phase code as the current active path unless the task is specifically to implement that phase.
- In `wiki_strict`, `/reconcile` and `/maintenance` are view-only projections (no file mutations) even in later phases.

## CI / Verification Gotchas

- `.github/workflows/wiki-lint.yml` invokes `python3 scripts/wiki_check.py`, `scripts/raw_manifest_check.py`, and `scripts/untracked_raw_check.py`.
- The `scripts/` directory is listed in `.gitignore` and does not exist in the repo. **These CI checks are currently non-functional.** Do not assume the scripts exist or try to create them unless the task explicitly requires fixing the CI workflow.

## Implementation Rules

Before editing, identify target behavior, target files, edit scope, test command, and rollback method.

Do not make unrelated refactors.

## Verification Rules

Every task must end with one of: unit test passed, integration test passed, smoke test passed, manual verification documented, or unable to verify with reason.

## Final Check

Before finishing, run `git status --short` and confirm no local task state, cache, or generated output is staged.
