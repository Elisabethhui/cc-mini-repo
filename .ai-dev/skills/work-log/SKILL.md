---
name: work-log
description: Use after review or commit to record a compact task result, verification evidence, risk, rollback point, and next step for future small-context sessions.
---

# Work Log

## Purpose

Record the outcome of one context-bounded task in a compact form that helps future sessions resume without re-reading the whole conversation.

A work log is not a diary, wiki, or full transcript. It is a short recovery artifact.

## File Boundary

Committed files:

- `.ai-dev/skills/work-log/SKILL.md`
- `.ai-dev/templates/WORK_LOG.md`

Local work logs belong in ignored paths:

- `.ai-dev/worklogs/task-xxx.md`

Do not commit generated work logs unless explicitly requested.

Never include secrets, API keys, raw environment values, or huge terminal output.

## Inputs

Use these inputs when available:

- current task file
- context pack
- test gate result
- review rollback result
- commit hash
- changed files
- known risk
- next suggested task

## What To Record

Keep only durable facts:

- task id and goal
- files changed
- code intelligence used
- tests or verification run
- review decision
- commit or rollback point
- remaining risk
- next recommended task

Do not record:

- full conversation
- raw command logs
- unrelated brainstorming
- generated cache content
- secrets
- long pasted diffs

## Process

1. Identify the task id and goal.
2. List changed files.
3. Summarize code intelligence used.
4. Summarize verification.
5. Summarize review decision.
6. Record commit hash or rollback point.
7. Record remaining risks.
8. Suggest exactly one next task when possible.
9. Keep the result short.

## Output Format

Write the work log with these sections:

- `# Work Log: task-xxx`
- `## Goal`
- `## Changed Files`
- `## Code Intelligence Used`
- `## Verification`
- `## Review Decision`
- `## Commit / Rollback Point`
- `## Remaining Risk`
- `## Next Task`

## Size Rule

Keep the work log under 100 lines unless the user explicitly asks for more detail.

If the log grows beyond 100 lines, summarize more aggressively.

## Quality Check

Before finishing, verify:

- It can help a future session resume.
- It does not include transient chatter.
- It does not include secrets.
- It names the commit or rollback point.
- It clearly says what should happen next.

## Stop Rules

Stop and ask the user if:

- the task result is unclear
- the commit hash is unknown
- tests were not run and risk is high
- the next task depends on a product decision