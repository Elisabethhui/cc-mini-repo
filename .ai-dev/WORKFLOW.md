# Context-Bounded Development Workflow

## Goal

Make coding tasks small, code-intelligence guided, context-bounded, testable, reviewable, reversible, and recoverable.

## Workflow

1. Macro-plan large goals.
2. Slice into one small task.
3. Use surface-search to find anchors.
4. Use code-intel to inspect precise code relationships.
5. Build a context pack with context tiers.
6. Implement only the current task.
7. Run map-sync after code changes.
8. Run test-gate.
9. Run fresh-review or review-rollback.
10. Record work-log.

## Context Modes

For 32k models: one behavior per task, up to 5 read files, up to 3 edit files, prefer snippets/signatures over full files, and stop if impact radius is broad.

Larger models may widen context, but testing, review, rollback, and file boundaries remain mandatory.

## REPL Workflow Commands

These read-only helpers are available inside the cc-mini REPL:

- `/workflow-status` — workflow readiness check
- `/workflow-init` — scaffold missing workflow files
- `/workflow-doctor` — read-only diagnostics
- `/workflow-test` — test recommendations from changed files

They do not modify source files, run tests automatically, or commit changes.

See `docs/workflow.md` for full user documentation.

## Recovery

To resume a future session, read in this order:

1. `AGENTS.md`
2. `.ai-dev/WORKFLOW.md`
3. `.ai-dev/PROJECT_MAP.md`
4. relevant local task/worklog if available
5. `git status --short`
