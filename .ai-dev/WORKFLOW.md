# Context-Bounded Development Workflow

This repository uses a small-context-friendly development workflow.

## Goal

Make coding tasks:

- small
- code-intelligence guided
- context-bounded
- testable
- reviewable
- reversible
- recoverable

## File Boundary

Committed workflow files:

- `AGENTS.md`
- `.ai-dev/README.md`
- `.ai-dev/WORKFLOW.md`
- `.ai-dev/templates/`
- `.ai-dev/skills/`

Ignored local task artifacts:

- `.ai-dev/tasks/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`

Ignored code intelligence indexes:

- `.codegraph/`
- `.codebase-memory/`

## Workflow

1. Slice the goal with `task-slicer`.
2. Locate relevant code with `code-intel`.
3. Build a task context with `context-pack`.
4. Implement only the current task.
5. Verify with `test-gate`.
6. Review and decide with `review-rollback`.
7. Record the result with `work-log`.

## Context Modes

For `32k` models:

- one behavior per task
- up to 5 read files
- up to 3 edit files
- prefer snippets over full files
- stop if impact radius is broad

For larger models:

- task size may grow slightly
- testing, review, and rollback still remain mandatory

## Code Intelligence

Prefer small CodeGraph queries:

```bash
codegraph query "<keyword>"
codegraph callers "<symbol>"
codegraph callees "<symbol>"
codegraph impact "<symbol>"
git diff --name-only | codegraph affected --stdin --quiet