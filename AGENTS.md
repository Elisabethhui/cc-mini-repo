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

Do not commit `.codegraph/` or `.codebase-memory/`.

## Code Reading Rules

Before reading large files:

1. Check the current task.
2. Use surface-search if there is no anchor.
3. Use code intelligence if available.
4. Use `rg` for exact search.
5. Read small snippets.
6. Read whole files only when necessary.

## Implementation Rules

Before editing, identify target behavior, target files, edit scope, test command, and rollback method.

Do not make unrelated refactors.

## Verification Rules

Every task must end with one of: unit test passed, integration test passed, smoke test passed, manual verification documented, or unable to verify with reason.

## Final Check

Before finishing, run `git status --short` and confirm no local task state, cache, or generated output is staged.
