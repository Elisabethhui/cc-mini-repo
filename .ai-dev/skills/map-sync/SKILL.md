---
name: map-sync
description: Use after implementation and before test selection or the next subtask to ensure local code intelligence maps are synced with the latest file changes.
---

# Map Sync

## Purpose

Ensure the code intelligence map reflects the current working tree after code changes.

This skill is a synchronization barrier between implementation and testing.

Do not run test selection, impact analysis, or the next subtask against a stale map.

## Why This Matters

After implementation, files may contain new functions, classes, imports, routes, or tests.

If CodeGraph or another code intelligence index is stale:

- affected tests may be wrong
- callers and callees may be missing
- the next task may not see newly created symbols
- review may underestimate impact
- the model may recreate code that already exists

## Workflow Position

Run map sync after:

- implementation
- code generation
- file move or rename
- public API changes
- new test files
- dependency/import changes

Run map sync before:

- `test-gate`
- `review-rollback`
- next subtask
- CodeGraph affected test selection
- impact analysis

## File Boundary

Committed files:

- `.ai-dev/skills/map-sync/SKILL.md`
- `.ai-dev/templates/MAP_SYNC.md`

Local sync notes belong in ignored paths:

- `.ai-dev/worklogs/`
- `.ai-dev/tmp/`

Never commit:

- `.codegraph/`
- `.codebase-memory/`
- raw sync logs
- local daemon state
- generated caches

## Inputs

Use these inputs when available:

- changed files from `git diff --name-only`
- current task file
- context pack
- implementation summary
- CodeGraph status
- CodeGraph sync result
- known generated files
- changed public symbols

## Sync Order

Use this order:

1. Check changed files.
2. Confirm whether code intelligence is installed and initialized.
3. Run or confirm sync.
4. Check status after sync.
5. Record whether the map is fresh enough for test selection.
6. If sync fails, fall back to `rg` and targeted file reads.
7. Do not continue to affected-test selection if map freshness is unknown.

## Suggested Commands

Use these commands when appropriate:

```bash
git diff --name-only
codegraph status
codegraph sync
codegraph status
git diff --name-only | codegraph affected --stdin --quiet
```

If CodeGraph is not available, record fallback:

```bash
rg -n "<changed symbol or keyword>"
```

## Freshness Rules

Map state must be classified as one of:

- `fresh`: sync succeeded or watcher confirmed current state
- `probably-fresh`: watcher is active and changed files are visible in queries
- `stale`: changed files are not reflected in code intelligence
- `unavailable`: code intelligence tool is not installed or not initialized
- `unknown`: freshness cannot be determined

Only `fresh` or `probably-fresh` may proceed to CodeGraph-based test selection.

If state is `stale`, `unavailable`, or `unknown`, use fallback search or stop.

## Changed File Rules

Treat these changes as requiring map sync:

- source file changed
- test file changed
- import changed
- route changed
- CLI command changed
- class/function/method added or removed
- file renamed or moved
- public interface changed

Changes that usually do not require map sync:

- local task notes
- work logs
- markdown-only workflow files
- ignored temp files
- generated caches

## Output Format

Write the map sync result with these sections:

- `# Map Sync: task-xxx`
- `## Changed Files`
- `## Sync Needed`
- `## Commands Run`
- `## Freshness`
- `## Affected Tests Check`
- `## Fallback Used`
- `## Decision`
- `## Notes`

Decision must be one of:

- `proceed-to-test-gate`
- `use-fallback-search`
- `stop-and-fix-sync`
- `skip-not-needed`

## Quality Check

Before finishing, verify:

- changed files were identified
- sync need was explicitly decided
- freshness was classified
- no local indexes were staged
- test selection does not rely on stale data
- fallback is named if CodeGraph is unavailable

## Stop Rules

Stop before test selection if:

- CodeGraph reports stale or missing index
- changed source files are not visible in queries
- sync command fails
- affected test output is empty but impact should not be empty
- `.codegraph/` or `.codebase-memory/` appears staged
- the task created new public symbols and the map cannot find them