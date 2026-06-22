---
name: workflow-runbook
description: Use when the user needs to run, explain, audit, or refine the full context-bounded development workflow across task slicing, code intelligence, context packing, testing, review, rollback, and logging.
---

# Workflow Runbook

## Purpose

Guide the full context-bounded development workflow from a large goal to a verified, reviewable, reversible task result.

Use this skill when coordinating multiple workflow skills or explaining what step should happen next.

## File Boundary

Committed files:

- `.ai-dev/skills/workflow-runbook/SKILL.md`
- `.ai-dev/WORKFLOW.md`

Local task artifacts belong in ignored paths:

- `.ai-dev/tasks/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`

Do not commit generated local task artifacts unless explicitly requested.

Never commit `.codegraph/` or `.codebase-memory/`.

## Workflow Order

Run the workflow in this order:

1. `task-slicer`
2. `code-intel`
3. `context-pack`
4. implementation
5. `test-gate`
6. `review-rollback`
7. `work-log`

Do not skip testing or review for code changes.

## Step Responsibilities

### 1. Task Slicer

Split a large goal into one small task.

Output:

- task id
- allowed read files
- allowed edit files
- acceptance criteria
- test plan
- rollback plan

### 2. Code Intel

Use CodeGraph or precise search to locate relevant structure before reading source.

Prefer:

- `codegraph query`
- `codegraph callers`
- `codegraph callees`
- `codegraph impact`
- `codegraph affected`

Use broad exploration only when smaller queries fail.

### 3. Context Pack

Compress task, code intelligence, snippets, constraints, tests, and exclusions into a small working packet.

The context pack must fit the selected model context.

### 4. Implementation

Change only what the task allows.

Rules:

- no unrelated refactor
- no broad formatting changes
- no generated/cache/local files
- no secrets
- update or add tests only when the task requires it

### 5. Test Gate

Run the smallest useful verification.

Prefer affected or targeted tests before broad suites.

### 6. Review Rollback

Review the task diff, test evidence, risk, and rollback path.

Decide:

- commit
- revise
- rollback
- reslice
- hold

### 7. Work Log

Record the result compactly for future sessions.

## Context Modes

Use task size based on model context:

- `32k`: one small behavior, up to 5 read files, up to 3 edit files
- `64k`: one medium behavior, up to 8 read files, up to 4 edit files
- `128k+`: larger context allowed, but still keep task, test, review, and rollback gates

Do not use larger context as an excuse to skip boundaries.

## Clean Repository Rules

Before committing, verify:

```bash
git status --short
git diff --stat
```

Never stage:

- `.ai-dev/tasks/`
- `.ai-dev/context-packs/`
- `.ai-dev/worklogs/`
- `.ai-dev/checkpoints/`
- `.ai-dev/tmp/`
- `.codegraph/`
- `.codebase-memory/`
- `__pycache__/`
- `*.pyc`

## Output Format

When explaining the current workflow state, use:

- `Current Step`
- `Completed`
- `Next Action`
- `Risk`
- `Stop Condition`

## Stop Rules

Stop and ask the user before continuing if:

- the branch has unrelated dirty files
- the next action would mix workflow files with product code
- secrets may be present
- tests are failing for unclear reasons
- task scope exceeds the selected context mode